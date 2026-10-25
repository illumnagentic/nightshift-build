import json
import logging
import re
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, FastAPI, Header, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException
from workers import WorkerEntrypoint
import asgi

import mubit
import prefs
import tfl

USERNAME_RE = re.compile(r"[A-Za-z0-9_-]{1,32}")

app = FastAPI()
# Routes sit on a router with prefix "/api", the base URL the web app proxies to.
api = APIRouter(prefix="/api")


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status, self.code, self.message = status, code, message


def error_response(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    return error_response(exc.status, exc.code, exc.message)


# Covers bad types, missing fields and malformed JSON: FastAPI reports all as validation errors.
@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return error_response(422, "invalid_request", "Request body is missing, malformed or has the wrong field types.")


# Routing 404s and 405s are raised as HTTPException; give them the contract shape, keeping headers like Allow.
@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException):
    code = {404: "not_found", 405: "method_not_allowed"}.get(exc.status_code, "http_error")
    response = error_response(exc.status_code, code, "No such endpoint." if exc.status_code == 404 else "Request not allowed.")
    response.headers.update(exc.headers or {})
    return response


# Middleware rather than an Exception handler: that route re-raises after responding, which the Workers adapter may not pass on.
@app.middleware("http")
async def internal_error_guard(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception:
        logging.exception("Unhandled error on %s %s", request.method, request.url.path)
        return error_response(500, "internal_error", "Something went wrong on the server.")


class NewUser(BaseModel):
    username: str


@api.get("/users")
async def list_users(request: Request):
    result = await request.scope["env"].DB.prepare(
        "SELECT user_id, username FROM users ORDER BY created_at, rowid"
    ).all()
    return {"users": [{"user_id": row["user_id"], "username": row["username"]} for row in result.results]}


@api.post("/users", status_code=201)
async def create_user(body: NewUser, request: Request):
    username = body.username.strip()
    if not USERNAME_RE.fullmatch(username):
        raise ApiError(422, "invalid_request", "Username must be 1 to 32 characters: letters, digits, _ or -.")
    user_id = "u_" + secrets.token_hex(8)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    try:
        await request.scope["env"].DB.prepare(
            "INSERT INTO users (user_id, username, created_at) VALUES (?, ?, ?)"
        ).bind(user_id, username, created_at).run()
    except Exception as exc:
        # The UNIQUE constraint decides, so two simultaneous requests cannot both win.
        if "UNIQUE constraint failed" in str(exc):
            raise ApiError(409, "username_taken", "That username is already taken.")
        raise
    return {"user_id": user_id, "username": username}


async def current_user(request: Request, x_user_id: str | None = Header(None)) -> str:
    """The user id from X-User-Id; 401 unknown_user when it is missing, empty or not a user."""
    if x_user_id:
        result = await request.scope["env"].DB.prepare("SELECT user_id FROM users WHERE user_id = ?").bind(x_user_id).all()
        if result.results:
            return x_user_id
    raise ApiError(401, "unknown_user", "No user with that id.")


def prefs_response(row) -> dict:
    """The GET /prefs body from a prefs row, or all-null when there is none."""
    if row is None:
        return {"text": None, "commute_postcode": None, "max_commute_min": None, "parsed": None, "commute_status": None}
    return {
        "text": row["text"],
        "commute_postcode": row["commute_postcode"],
        "max_commute_min": row["max_commute_min"],
        "parsed": json.loads(row["parsed_json"]),
        "commute_status": row["commute_status"],
    }


async def prefs_row(db, user_id: str):
    result = await db.prepare("SELECT * FROM prefs WHERE user_id = ?").bind(user_id).all()
    return result.results[0] if result.results else None


@api.get("/prefs")
async def get_prefs(request: Request, user_id: str = Depends(current_user)):
    env = request.scope["env"]
    row = await prefs_row(env.DB, user_id)
    if row is not None and row["commute_status"] == "pending":
        # Each poll does one bounded batch of TfL calls; the contract already has the client polling.
        status, streak = await tfl.run_batch(
            env.DB, getattr(env, "TFL_BASE", None) or tfl.TFL_BASE, json.loads(row["parsed_json"])["hard"],
            row["commute_postcode"], row["commute_fail_streak"],
        )
        # Skip the write if the user re-saved prefs while the batch ran.
        await env.DB.prepare(
            "UPDATE prefs SET commute_status = ?, commute_fail_streak = ? WHERE user_id = ? AND updated_at = ? AND commute_status = 'pending'"
        ).bind(status, streak, user_id, row["updated_at"]).run()
        row = await prefs_row(env.DB, user_id)
    return prefs_response(row)


@api.put("/prefs")
async def put_prefs(request: Request, body: dict = Body(...), user_id: str = Depends(current_user)):
    text, postcode, max_commute = body.get("text"), body.get("commute_postcode"), body.get("max_commute_min")
    if not isinstance(text, str) or not text.strip():
        raise ApiError(422, "invalid_request", "text is required and must not be blank.")
    if postcode is not None and not isinstance(postcode, str):
        raise ApiError(422, "invalid_request", "commute_postcode must be a string.")
    # A JSON true is a Python int, so bool is refused by name.
    if max_commute is not None and (isinstance(max_commute, bool) or not isinstance(max_commute, int) or not 1 <= max_commute <= 180):
        raise ApiError(422, "invalid_request", "max_commute_min must be a whole number from 1 to 180.")
    if postcode is None and max_commute is not None:
        raise ApiError(422, "invalid_request", "max_commute_min needs a commute_postcode.")
    # Commute is optional: with no postcode the row keeps NULL postcode and status, and no TfL work runs.
    normalised = None
    if postcode is not None:
        normalised = prefs.normalise_postcode(postcode)
        if normalised is None:
            raise ApiError(422, "invalid_postcode", "commute_postcode must be a full UK postcode such as EC2N 2DB.")
    status = "pending" if normalised else None

    env = request.scope["env"]
    # Parse first, write after: a failed parse leaves the saved prefs as they were.
    try:
        result = await mubit.generate_content(
            env.MUBIT_API_KEY, prefs.MODEL, prefs.build_parse_body(text), getattr(env, "GEMINI_BASE", None) or mubit.GEMINI_BASE
        )
    except Exception as exc:
        logging.warning("Prefs parser call failed: %s: %s", type(exc).__name__, exc)
        raise ApiError(502, "parse_failed", "We could not read your preferences. Please try again.")
    parsed = prefs.parse_reply(result.data, max_commute)
    if parsed is None:
        logging.warning("Prefs parser reply unusable, request_id=%s", result.request_id)
        raise ApiError(502, "parse_failed", "We could not read your preferences. Please try again.")

    updated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    await env.DB.prepare(
        "INSERT INTO prefs (user_id, text, commute_postcode, max_commute_min, parsed_json, parse_request_id,"
        " commute_status, commute_fail_streak, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)"
        " ON CONFLICT(user_id) DO UPDATE SET text = excluded.text, commute_postcode = excluded.commute_postcode,"
        " max_commute_min = excluded.max_commute_min, parsed_json = excluded.parsed_json,"
        " parse_request_id = excluded.parse_request_id, commute_status = excluded.commute_status, commute_fail_streak = 0,"
        " updated_at = excluded.updated_at"
    ).bind(user_id, text, normalised, max_commute, json.dumps(parsed), result.request_id, status, updated_at).run()
    return {"text": text, "commute_postcode": normalised, "max_commute_min": max_commute, "parsed": parsed, "commute_status": status}


app.include_router(api)


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return await asgi.fetch(app, request.js_object, self.env)
