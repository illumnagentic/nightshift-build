#!/usr/bin/env bash
# Local dev helper: reseed the D1, add new tables, or start backend and frontend.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

in_use() { [ -n "$(ss -ltnH "sport = :$1")" ]; }

refuse_if_in_use() {
  for port in "$@"; do
    if in_use "$port"; then
      echo "dev.sh: port $port is in use. Stop whatever listens on it first." >&2
      exit 1
    fi
  done
}

case "${1:-}" in
  seed)
    refuse_if_in_use 8787
    exec "$root/worker/scripts/seed.sh"
    ;;
  tables)
    refuse_if_in_use 8787
    cd "$root/worker"
    exec npx --yes wrangler d1 execute haka --local --file schema.sql
    ;;
  start)
    [ -f "$root/worker/.dev.vars" ] || { echo "dev.sh: worker/.dev.vars is missing. Put MUBIT_API_KEY=... in it." >&2; exit 1; }
    [ -d "$root/web/node_modules" ] || { echo "dev.sh: web/node_modules is missing. Run: cd web && npm ci" >&2; exit 1; }
    refuse_if_in_use 8787 5173
    # setsid gives each child its own process group, so one kill reaches its descendants
    # (workerd under pywrangler, vite under npm).
    (cd "$root/worker" && exec setsid uvx --from workers-py pywrangler dev) &
    backend=$!
    (cd "$root/web" && exec setsid npm run dev) &
    frontend=$!
    stop() {
      trap '' INT TERM EXIT
      kill -TERM -- "-$backend" "-$frontend" 2>/dev/null || true
      wait 2>/dev/null || true
    }
    trap stop INT TERM EXIT
    wait -n
    ;;
  *)
    echo "usage: ./dev.sh seed|tables|start" >&2
    exit 1
    ;;
esac
