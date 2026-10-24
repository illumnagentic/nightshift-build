# Auto-complete probe

One live call, made with `fetch_rapidapi.py autocomplete --query Brighton --cap 300`.
Metadata only: no response body, no key.

| Field | Value |
| ----- | ----- |
| Timestamp (UTC) | 2026-10-24T10:00:16+00:00 |
| Host | uk-real-estate-rightmove.p.rapidapi.com |
| Endpoint | GET /auto-complete |
| Params | `location=Brighton` |
| HTTP status | 200 |
| Bytes | 3117 |
| `x-ratelimit-requests-remaining` | 297 |
| Top-level keys | `data`, `status`, `message` |
| `data` | list of 10 objects |
| `data[i]` keys | `id`, `type`, `displayName`, `highlighting`, `highlights`, `locationIdentifier` |
| Example `locationIdentifier` | `REGION^93554` (displayName "Brighton, East Sussex") |

Other identifier types seen: `STATION^<n>`. Live calls in this step: 1 of 2 allowed.
