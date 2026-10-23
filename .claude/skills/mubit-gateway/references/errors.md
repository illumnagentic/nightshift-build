# Mubit error codes

Verified 23 Oct 2026 from `https://docs.mubit.ai/troubleshooting.md`. Re-check there.

All of these carry `type: middleware_gateway_error` in the provider's error format
(Gemini: the code is the `reason` of the `ErrorInfo` detail).

## Key errors

| Code                                                                 | Status | Fix                                                                                                               |
| -------------------------------------------------------------------- | ------ | ----------------------------------------------------------------------------------------------------------------- |
| `missing_key`                                                        | 401    | No key sent. Is `MUBIT_API_KEY` set in the Worker env?                                                            |
| `invalid_key`                                                        | 401    | Wrong, revoked or malformed key, or two different Mubit keys. Check base URL too.                                 |
| `wrong_region`                                                       | 401    | Use the base URL the message (and console Connect page) names.                                                    |
| `key_expired`                                                        | 401    | Create or rotate a key.                                                                                           |
| `key_permission`                                                     | 403    | Read-only key. Use an Inference key.                                                                              |
| `key_scope`                                                          | 403    | Key not tied to this project.                                                                                     |
| `provider_key_refused`                                               | 401    | A provider key was sent instead of the Mubit key. Put the provider key in the console.                            |
| `subscription_token_refused` / `jwt_refused` / `oauth_token_refused` | 401    | A sign-in token was sent. Use the Mubit key.                                                                      |
| `extra_credential_refused`                                           | 401    | Another credential beside the Mubit key. Unset `ANTHROPIC_AUTH_TOKEN` (SDK) or `ANTHROPIC_API_KEY` (Claude Code). |
| `middleware_key_refused`                                             | 401    | Mubit key in the wrong place (another header, the path).                                                          |
| `engine_unavailable`                                                 | 503    | Wait `retry-after`.                                                                                               |

## Provider key errors

| Code                          | Status | Fix                                                                           |
| ----------------------------- | ------ | ----------------------------------------------------------------------------- |
| `provider_key_missing`        | 403    | No key for that provider in the console, and starter credit doesn't cover it. |
| `provider_region_unavailable` | 403    | Delete and re-add the provider key.                                           |
| `key_store_unavailable`       | 503    | Wait `retry-after`.                                                           |

## Starter credit errors

| Code                         | Status      | Fix                                                                                                |
| ---------------------------- | ----------- | -------------------------------------------------------------------------------------------------- |
| `starter_credit_used_up`     | 402         | Add own provider key.                                                                              |
| `starter_credit_model`       | 400         | Use a model the message lists.                                                                     |
| `starter_credit_route`       | 403         | Path not served on credit.                                                                         |
| `starter_credit_tools`       | 400         | Hosted tools / background mode not on credit.                                                      |
| `starter_credit_option`      | 400         | Drop the option the message names.                                                                 |
| `starter_credit_body`        | 413/408/400 | Body > 8 MiB, slower than 60 s, or not plain JSON.                                                 |
| `starter_credit_key_refused` | 502         | Add own provider key.                                                                              |
| `starter_credit_busy`        | 429         | Too many calls in flight. Wait `retry-after`, send fewer in parallel. Matters for persona batches. |
| `starter_credit_unavailable` | 503         | Wait `retry-after`.                                                                                |

## Path errors

| Code                     | Status | Fix                                                                         |
| ------------------------ | ------ | --------------------------------------------------------------------------- |
| `unknown_route`          | 404    | Path outside `/openai/v1`, `/anthropic`, `/gemini`, `/compat/{service}/v1`. |
| `unknown_provider`       | 404    | `/compat/{service}` must be openrouter, groq, together or mistral.          |
| `admin_path_refused`     | 403    | Provider admin endpoints: call the provider directly.                       |
| `invalid_path`           | 400    | `.`/`..` segment, `;`, control char, or double-encoded escape.              |
| `no_provider_configured` | 503    | Call went to the console address. Type is `middleware_error`.               |

## Connection errors

| Code                                      | Status | Fix                                                      |
| ----------------------------------------- | ------ | -------------------------------------------------------- |
| `upstream_unreachable`                    | 502    | Nothing sent. Retry.                                     |
| `upstream_failed`                         | 502    | Provider may have it. Retry only if a duplicate is safe. |
| `upstream_redirect`                       | 502    | Wrong path. Retrying won't help.                         |
| `upstream_timeout`                        | 504    | Provider didn't start within 610 s. Stream long answers. |
| `gateway_overloaded` / `gateway_draining` | 503    | Nothing sent. Retry.                                     |
