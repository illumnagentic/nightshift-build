import logging
import re
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException
from workers import WorkerEntrypoint
import asgi

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
    return error_response(422, "invalid_request", "Request body must be JSON like {\"username\": \"alex\"}.")


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


app.include_router(api)


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return await asgi.fetch(app, request.js_object, self.env)
