# Worker skeleton, local D1 and seed script: run evidence

Date: 2026-10-24. Metadata only.

Tools: pywrangler 1.17.9 (`uvx --from workers-py pywrangler`), wrangler 4.152.0
(`npx wrangler`, node v25.2.1), uv, system python 3.12.3 (Worker runtime is Python 3.13).

## Seed

- `worker/scripts/seed.sh` (fresh): exit 0.
- `cd /tmp && /home/iamzsolt/PROJECTS/haka/worker/scripts/seed.sh` (re-run, other cwd): exit 0.

Counts on the local D1 afterwards, via
`npx wrangler d1 execute haka --local --json --command "SELECT ..."`:

- `SELECT count(*) FROM listings`: 635
- `SELECT count(*) FROM users`: 0

## Dev server

- `cd worker && uvx --from workers-py pywrangler dev` (background): "Ready on http://localhost:8787".
- `curl -s -o /dev/null -w '%{http_code}' http://localhost:8787/docs`: 200
- `GET /openapi.json`: 200
- Server stopped afterwards; port 8787 returns no response.
