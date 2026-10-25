"""Turn each listing's photos and floorplans into text flags with Gemini, through Mubit.

One request per listing: every downloaded image (see fetch_images.py and
images-manifest.csv) is sent inline with a label giving its index and kind. The model
returns one JSON entry per image, which is mapped into flag rows shaped as in
docs/api-contract.md (photo_flags). Not trained; only the Mubit key is sent.

photo_flags.jsonl holds two kinds of line:
  - flag rows: flag_id, listing_id, scope, field, value, observation, source_photo,
    confidence, uncertainty, room, corrected_text.
  - one status line per finished listing, with "record_type": "listing_status":
    request_id, model_version, usage, skipped photos, images left out of the request,
    images the model did not answer for, and rows rejected for breaking an enum.
A listing with a status line is complete and is not sent again. A listing whose call
fails writes nothing, so the next run retries it.

Images are sent as their real type, read from the file's first bytes, not from the
extension. Any other type is left out of the request and listed as unsupported_format in
the status line, so the rest of the listing is still flagged.

Usage (from the dataset/ directory):
  python3 -I -B scripts/flag_images.py [--limit N] [--listing ID ...] [--workers 4]
MUBIT_API_KEY is read from the environment, else from the repo-root .env.
"""
import argparse
import base64
import concurrent.futures
import csv
import json
import os
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "worker", "src"))
from mubit import MubitError, build_request, parse_response  # noqa: E402

MODEL = "gemini-3.5-flash-lite"
MEDIA_RESOLUTION = "MEDIA_RESOLUTION_MEDIUM"
THINKING = {"thinkingLevel": "minimal"}
TIMEOUT = 300
MAX_OUTPUT_TOKENS = 16384
# GIF is not in Gemini's documented list, but a live call accepted a GIF floorplan and read
# it (see evidence/photo-flags/step-2.md), so it is sent.
SENDABLE = {"image/png", "image/jpeg", "image/webp", "image/heic", "image/heif", "image/gif"}

ROOMS = ("living_room", "kitchen", "bedroom", "bathroom", "hallway", "garden", "exterior", "other")
LIGHTS = ("none", "poor", "ok", "bright")
CONFIDENCES = ("high", "medium", "low")
FIELDS_BY_SCOPE = {"photo": ("room", "light", "size_tricks", "defects", "missing"),
                   "listing": ("floorplan_notes", "sqm_estimate")}

SYSTEM_INSTRUCTION = (
    "You describe estate-agent images of a home for sale in the UK. You are given numbered "
    "images, each preceded by a label with its index and kind (photo or floorplan). Return "
    "one entry per image, using the same index. Report only what you can see. Never guess "
    "what is not visible; use low confidence and say what is uncertain instead.\n"
    "For a photo: set skip to true if it is an agent logo, a duplicate of another image in "
    "this request, or not a photo of the property (a map, an energy chart, a stock image); "
    "give skip_reason and leave the other fields out. Otherwise you must always give both "
    "room (one of the allowed values) and light (none, poor, ok or bright, judged from "
    "windows and brightness), and also the lists size_tricks (things that make the space look bigger or smaller than it "
    "is, such as wide-angle distortion or sparse furniture), defects (visible damp, mould, "
    "cracks, and also minor defects: worn or stained carpet, scuffed walls, dated or tired "
    "fittings, damp marks, clutter; use low confidence when unsure) and missing (things a buyer would expect to see that the photo "
    "shows are absent, such as no window or no storage). Lists may be empty.\n"
    "For a floorplan: give floorplan_notes (short facts about layout, room count, "
    "orientation of rooms, awkward shapes) and sqm_estimate (total floor area in square "
    "metres, from stated areas or dimensions, or null if you cannot tell). For a photo, "
    "floorplan_notes is empty and sqm_estimate is null; for a floorplan, room and light are null "
    "and the photo lists are empty.\n"
    "Every flag has a value (short text), an observation (what you saw), a confidence "
    "(high, medium or low) and an uncertainty. Uncertainty names what limits your judgement (the angle, the lighting, "
    "editing of the photo, only part of the room in view); it is null only when nothing limits "
    "it. Low confidence is expected when a photo is ambiguous."
)


def _flag_schema(value_type="STRING", value_enum=None, nullable_value=False):
    value = {"type": value_type}
    if value_enum:
        value["enum"] = list(value_enum)
    if nullable_value:
        value["nullable"] = True
    return {"type": "OBJECT", "properties": {
        "value": value, "observation": {"type": "STRING"},
        "confidence": {"type": "STRING", "enum": list(CONFIDENCES)},
        "uncertainty": {"type": "STRING", "nullable": True}},
        "required": ["value", "observation", "confidence", "uncertainty"]}


def _flag_list():
    return {"type": "ARRAY", "items": _flag_schema()}


def _nullable(schema):
    return dict(schema, nullable=True)


# Every key is required: with optional keys the model left out light and the lists.
# Keys that do not apply to an image (room on a floorplan, say) come back null or empty.
RESPONSE_SCHEMA = {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
    "index": {"type": "INTEGER"},
    "skip": {"type": "BOOLEAN"},
    "skip_reason": {"type": "STRING", "nullable": True},
    "room": _nullable(_flag_schema(value_enum=ROOMS)),
    "light": _nullable(_flag_schema(value_enum=LIGHTS)),
    "size_tricks": _flag_list(), "defects": _flag_list(), "missing": _flag_list(),
    "floorplan_notes": _flag_list(),
    "sqm_estimate": _nullable(_flag_schema("NUMBER", nullable_value=True)),
}, "required": ["index", "skip", "skip_reason", "room", "light", "size_tricks", "defects", "missing",
                "floorplan_notes", "sqm_estimate"]}}


def load_env_key(env_path):
    key = os.environ.get("MUBIT_API_KEY")
    if key:
        return key
    try:
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("export "):
                    line = line[7:]
                name, sep, value = line.partition("=")
                if sep and name.strip() == "MUBIT_API_KEY":
                    return value.strip().strip("'\"") or None
    except OSError:
        pass
    return None


def sniff_mime(data):
    """MIME type from the file's first bytes; None when unknown."""
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if data[4:8] == b"ftyp":
        brand = data[8:12]
        if brand in (b"heic", b"heix", b"hevc", b"hevx"):
            return "image/heic"
        if brand in (b"mif1", b"msf1", b"heif"):
            return "image/heif"
    return None


def load_images(dataset):
    """{listing_id: [manifest rows]} for downloaded images, photos first, in position order."""
    by_listing = {}
    with open(os.path.join(dataset, "images-manifest.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["status"] == "ok":
                r["position"] = int(r["position"])
                by_listing.setdefault(r["listing_id"], []).append(r)
    for rows in by_listing.values():
        rows.sort(key=lambda r: (r["kind"] != "photo", r["position"]))
    return dict(sorted(by_listing.items()))


def build_body(dataset, images, drop_gif=False):
    """Return (request body, sent, unsupported). sent[i] is the manifest row labelled index i.
    With drop_gif, GIFs are left out and listed as rejected_by_model."""
    parts, sent, unsupported = [], [], []
    for r in images:
        with open(os.path.join(dataset, r["path"]), "rb") as f:
            data = f.read()
        mime = sniff_mime(data)
        if drop_gif and mime == "image/gif":
            unsupported.append({"url": r["url"], "reason": "rejected_by_model", "mime": mime})
            continue
        if mime not in SENDABLE:
            unsupported.append({"url": r["url"], "reason": "unsupported_format", "mime": mime})
            continue
        parts.append({"text": f"Image {len(sent)} ({r['kind']}):"})
        parts.append({"inlineData": {"mimeType": mime, "data": base64.b64encode(data).decode("ascii")}})
        sent.append(r)
    config = {"responseMimeType": "application/json", "responseSchema": RESPONSE_SCHEMA,
              "temperature": 0, "mediaResolution": MEDIA_RESOLUTION, "maxOutputTokens": MAX_OUTPUT_TOKENS}
    if THINKING:
        config["thinkingConfig"] = THINKING
    body = {"systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
            "contents": [{"role": "user", "parts": parts}], "generationConfig": config}
    return body, sent, unsupported


def check_row(row):
    """Return a reason string if the row breaks the contract, else None."""
    if row["scope"] not in FIELDS_BY_SCOPE:
        return f"scope {row['scope']!r}"
    if row["field"] not in FIELDS_BY_SCOPE[row["scope"]]:
        return f"field {row['field']!r} for scope {row['scope']}"
    if row["scope"] == "photo":
        if row["room"] not in ROOMS:
            return f"room {row['room']!r}"
        if row["field"] == "light" and row["value"] not in LIGHTS:
            return f"light value {row['value']!r}"
    elif row["room"] is not None:
        return "room set on listing scope"
    if row["field"] == "sqm_estimate":
        v = row["value"]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or v <= 0:
            return f"sqm_estimate value {v!r}"
    elif not isinstance(row["value"], str) or not row["value"].strip():
        return f"value {row['value']!r}"
    if row["confidence"] not in CONFIDENCES:
        return f"confidence {row['confidence']!r}"
    if not isinstance(row["observation"], str):
        return "observation not text"
    if row["uncertainty"] is not None and not isinstance(row["uncertainty"], str):
        return "uncertainty not text"
    return None


def map_response(listing_id, sent, entries):
    """Map the model's per-image entries to (flag rows, skipped, unanswered urls, rejected)."""
    rows, skipped, rejected = [], [], []
    by_index = {}
    for e in entries:
        if isinstance(e, dict) and isinstance(e.get("index"), int) and 0 <= e["index"] < len(sent):
            by_index.setdefault(e["index"], e)
    for i, img in enumerate(sent):
        e = by_index.get(i)
        if e is None:
            continue
        if e.get("skip") is True:
            skipped.append({"url": img["url"], "reason": str(e.get("skip_reason") or "")})
            continue
        scope = "photo" if img["kind"] == "photo" else "listing"
        room_flag = e.get("room") if isinstance(e.get("room"), dict) else {}
        for field in FIELDS_BY_SCOPE[scope]:
            items = e.get(field)
            if items is None:
                continue
            if field in ("room", "light", "sqm_estimate"):
                items = [items]
            elif not isinstance(items, list):
                rejected.append({"url": img["url"], "field": field, "reason": "not a list"})
                continue
            for n, item in enumerate(items):
                if not isinstance(item, dict):
                    rejected.append({"url": img["url"], "field": field, "reason": "item not an object"})
                    continue
                if field == "sqm_estimate" and item.get("value") is None:
                    continue
                value, unc = item.get("value"), item.get("uncertainty")
                row = {"flag_id": f"{listing_id}:{img['kind']}-{img['position']}:{field}:{n}",
                       "listing_id": listing_id, "scope": scope, "field": field,
                       "value": value.strip() if isinstance(value, str) else value,
                       "observation": item.get("observation"),
                       "source_photo": img["url"], "confidence": item.get("confidence"),
                       "uncertainty": (unc.strip() or None) if isinstance(unc, str) else unc,
                       "room": room_flag.get("value") if scope == "photo" else None,
                       "corrected_text": None}
                reason = check_row(row)
                if reason:
                    rejected.append({"url": img["url"], "field": field, "reason": reason})
                else:
                    rows.append(row)
    unanswered = [sent[i]["url"] for i in range(len(sent)) if i not in by_index]
    return rows, skipped, unanswered, rejected


def post(url, headers, payload):
    req = urllib.request.Request(url, data=payload.encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, dict(resp.headers.items()), resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers.items()), e.read().decode("utf-8", "replace")


def response_entries(data):
    cand = (data.get("candidates") or [{}])[0]
    text = "".join(p.get("text", "") for p in (cand.get("content") or {}).get("parts") or [])
    entries = json.loads(text)
    if not isinstance(entries, list):
        raise ValueError(f"response is not a list (finishReason {cand.get('finishReason')})")
    return entries


def flag_listing(dataset, api_key, listing_id, images, sender=post):
    """Send one listing. Returns the output lines (dicts). Raises on any call or parse failure."""
    body, sent, unsupported = build_body(dataset, images)
    if not sent:
        raise ValueError("no sendable images")
    url, headers, payload = build_request(api_key, MODEL, body)
    try:
        result = parse_response(*sender(url, headers, payload))
    except MubitError as e:
        # The model may refuse GIF input; resend once without the GIFs rather than lose the listing.
        if e.status != 400 or not any(
                p.get("inlineData", {}).get("mimeType") == "image/gif" for p in body["contents"][0]["parts"]):
            raise
        body, sent, unsupported = build_body(dataset, images, drop_gif=True)
        if not sent:
            raise
        url, headers, payload = build_request(api_key, MODEL, body)
        result = parse_response(*sender(url, headers, payload))
    rows, skipped, unanswered, rejected = map_response(listing_id, sent, response_entries(result.data))
    usage = result.data.get("usageMetadata") or {}
    status = {"record_type": "listing_status", "listing_id": listing_id, "request_id": result.request_id,
              "model": MODEL, "model_version": result.data.get("modelVersion"),
              "usage": {k: usage.get(k) for k in ("promptTokenCount", "candidatesTokenCount",
                                                  "thoughtsTokenCount", "totalTokenCount")},
              "images_sent": len(sent), "skipped": skipped, "unsupported_format": unsupported,
              "unanswered": unanswered, "rejected": rejected}
    return rows + [status]


def completed(out_path):
    done = set()
    try:
        with open(out_path, encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                if rec.get("record_type") == "listing_status":
                    done.add(rec["listing_id"])
    except FileNotFoundError:
        pass
    return done


def run(dataset, api_key, out_path, workers=4, limit=None, only=None, sender=post):
    listings = load_images(dataset)
    ids = list(listings)
    if only:
        ids = [i for i in ids if i in set(only)]
    if limit is not None:
        ids = ids[:limit]
    done = completed(out_path)
    todo = [i for i in ids if i not in done]
    summary = {"selected": len(ids), "already_done": len(ids) - len(todo), "ok": 0, "failed": []}
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex, \
            open(out_path, "a", encoding="utf-8") as out:
        futures = {ex.submit(flag_listing, dataset, api_key, i, listings[i], sender): i for i in todo}
        for fut in concurrent.futures.as_completed(futures):
            lid = futures[fut]
            try:
                lines = fut.result()
            except Exception as e:  # nothing written; retried next run
                summary["failed"].append((lid, f"{type(e).__name__}: {e}"))
                continue
            out.write("".join(json.dumps(line, ensure_ascii=False) + "\n" for line in lines))
            out.flush()
            summary["ok"] += 1
            for r in lines[-1]["rejected"]:
                print(f"REJECTED {lid} {r['field']} {r['reason']}", file=sys.stderr)
    return summary


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dataset", default=".")
    ap.add_argument("--out", default=None, help="default <dataset>/photo_flags.jsonl")
    ap.add_argument("--limit", type=int, help="only the first N listings in id order")
    ap.add_argument("--listing", action="append", help="only this listing id (repeatable)")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    key = load_env_key(os.path.join(a.dataset, "..", ".env"))
    if not key:
        print("MUBIT_API_KEY not set in the environment or the repo-root .env", file=sys.stderr)
        return 2
    out = a.out or os.path.join(a.dataset, "photo_flags.jsonl")
    s = run(a.dataset, key, out, a.workers, a.limit, a.listing)
    print(f"selected {s['selected']}  already done {s['already_done']}  ok {s['ok']}  failed {len(s['failed'])}")
    for lid, err in sorted(s["failed"]):
        print(f"FAILED {lid} {err}")
    return 1 if s["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
