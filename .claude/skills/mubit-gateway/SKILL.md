---
name: mubit-gateway
description: Route an LLM call through Mubit correctly from this project's Python backend (Cloudflare Python Worker or plain FastAPI host). Use when writing or reviewing any code that creates an OpenAI, Anthropic or Gemini client, sets a base URL or MUBIT_API_KEY, calls api.mubit.ai, handles a 401/403/404 from an LLM call, sees an error with type `middleware_gateway_error` or a code such as `missing_key`, `extra_credential_refused`, `provider_key_missing` or `starter_credit_model`, or needs the `x-middleware-request-id` of a call. Also use before adding `mubit-sdk` (PyPI) or `@mubit-ai/sdk` (don't), or if anyone suggests calling an LLM from the TypeScript frontend (don't).
---

# Mubit gateway

Read from `https://docs.mubit.ai/llms-full.txt` on 23 Oct 2026 and probed without a key.
The code snippets are copied from the docs and have not been run in this repo. Mubit's docs change.
If anything below fails, re-read the source before trusting this file:

```bash
curl -sL https://docs.mubit.ai/llms-full.txt | less    # whole docs, one file
curl -sL https://docs.mubit.ai/reference/api.md        # any page: append .md
```

## What Mubit is, on the wire

Mubit is a proxy. Your server sends the same request it would send to OpenAI, Anthropic
or Gemini, but to Mubit's host and with a Mubit key. Mubit swaps in the provider key held
in its console, forwards the call, records the request and reply, and passes the answer
back. **Model IDs do not change.** There is no Mubit SDK needed for this.

## Base URLs — they differ per SDK

| Client (Python)                        | Base URL                                                                |
| -------------------------------------- | ----------------------------------------------------------------------- |
| `openai`                               | `https://api.mubit.ai/openai/v1`                                        |
| `anthropic`                            | `https://api.mubit.ai/anthropic` (**no** `/v1`, the SDK adds it)        |
| `google-genai`                         | `https://api.mubit.ai/gemini` (**no** `/v1beta`)                        |
| `openai` against Gemini                | `https://api.mubit.ai/gemini/v1beta/openai` (refused on starter credit) |
| OpenRouter / Groq / Together / Mistral | `https://api.mubit.ai/compat/{service}/v1`                              |
| Plain HTTPS POST                       | Full path, e.g. `https://api.mubit.ai/openai/v1/chat/completions`       |

The docs show these base URLs for the JS SDKs. The Python SDKs build request paths the
same way, so the same values should apply. _Unverified until the first call succeeds._

The console's **Connect** page shows the base URL for the workspace. If it differs from
the table, the console wins (`wrong_region` 401 names the right one).

## Keys

- The app sends **one key only: the Mubit key** (`mbt_…`), in the header the provider SDK
  already uses: `Authorization: Bearer` (OpenAI), `x-api-key` (Anthropic), `x-goog-api-key`
  (Gemini; never `?key=`).
- Provider keys (Gemini, Anthropic…) live in the Mubit console under **Provider keys**,
  not in our code or Worker secrets.
- **A second credential beside the Mubit key gets a 401.** With the Anthropic SDK, a stray
  `ANTHROPIC_AUTH_TOKEN` is sent too: unset it. A Google key in `GOOGLE_API_KEY` beats
  `GEMINI_API_KEY`.
- Keys are backend secrets: on a Python Worker, `wrangler secret put MUBIT_API_KEY`
  (locally in `.dev.vars`); on a FastAPI host, an environment variable from `.env`.
  Never in `wrangler.toml`, never in the frontend bundle, never committed.
- Two key permissions: **Inference** (send calls) and **Read only** (refused with
  `403 key_permission`). The app needs Inference.

## Server-side only

**The API answers no CORS preflight.** A browser call fails. All LLM calls go from the
Python backend; the TypeScript frontend only ever calls our own API. That also keeps the
key off users' devices.

## In the Python backend

- Use the provider SDK with `base_url`, or a plain HTTPS POST. Both work: it is just HTTPS.
- **Python Workers run on Pyodide.** Whether the `openai` / `google-genai` packages import
  and make requests there is _unverified_. The Backend host spike in
  `docs/decisions.md` checks it with one real call. If the SDK fights the runtime, send
  a plain HTTPS POST with the same URL, header and body instead, or move to the FastAPI host.
- **Do not add `mubit-sdk` (PyPI) or `@mubit-ai/sdk`.** Their memory / lessons routes
  (`/v2/control/*`) are not served by `api.mubit.ai` today (see `mubit-task-design`), and
  the gateway needs no SDK. Any new package is a new dependency anyway: ask the human first.

Minimal shapes (not run in this repo; swap per table):

```python
# Curator: OpenAI format, async (Python Workers handlers are async)
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=env.MUBIT_API_KEY, base_url="https://api.mubit.ai/openai/v1")
```

```python
# Photo flags: Gemini
from google import genai
from google.genai import types

client = genai.Client(
    api_key=env.MUBIT_API_KEY,
    http_options=types.HttpOptions(base_url="https://api.mubit.ai/gemini"),
)
```

## Record the request ID

**Every answer carries `x-middleware-request-id`** (`mreq_` + 32 hex), on success, stream
and error alike. Store it in D1 against our own `decision_id`. It is the only link from
our swipe/feedback rows back to the call in Mubit's **Requests** page, and support asks
for it. (The console's own "Request" ID under Details is a different ID.)

```python
# openai SDK: the raw response exposes headers
raw = await client.chat.completions.with_raw_response.create(
    model=CURATOR_MODEL,
    messages=messages,
    metadata={"session_id": session_id},
)
mubit_request_id = raw.headers.get("x-middleware-request-id")
completion = raw.parse()
```

With a plain HTTPS POST, read the `x-middleware-request-id` response header.

## Headers Mubit reads (and strips before forwarding)

| Header                                         | Effect                                                                 |
| ---------------------------------------------- | ---------------------------------------------------------------------- |
| `x-middleware-store: false`                    | Keeps a record without request or reply. **Such a call never trains.** |
| `x-middleware-record: full \| metadata \| off` | `metadata` = same as above. `off` also drops the task fingerprint.     |

Use them for calls that should not train or should not be stored (e.g. anything with
real personal data). A header can only lower what is kept. Default: everything is kept.

## Starter credit

If the console offers a starter credit, it serves **a fixed list of models**. Any other
model gets `400 starter_credit_model`, and the message lists the allowed IDs. Before
building on a model ID (e.g. a Gemini Flash-Lite), send one call and read the answer.
The starter credit also refuses hosted tools (web search etc.), bodies over 8 MiB and
non-JSON bodies. Adding our own provider key in the console removes these limits.

## Telling Mubit's errors from the provider's

- `type` is `middleware_gateway_error` (or `middleware_error`) → Mubit refused it. The
  `code` says why. Full table: [references/errors.md](references/errors.md).
- No such type, but `x-middleware-request-id` present → the provider's own error, passed on.
- No `x-middleware-request-id` at all → the call never reached Mubit. Check the base URL.
- `x-should-retry: false` → don't retry. `retry-after` on 429/503 → wait that long.
- Mubit retries only when it could not connect at all. It never resends a started call.

## Limits

Connect 10 s · first byte 610 s · silence 15 min · total 60 min. SDK default timeouts
(600 s) usually fire first. Mubit records up to 32 MiB of a request, and the first 4 MiB and last 256 KiB of a reply.
