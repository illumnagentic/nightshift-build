#!/usr/bin/env bash
# Rebuild the local D1 from scratch: listings schema, app schema, listings data.
set -euo pipefail

worker_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_dir="$(dirname "$worker_dir")"
cd "$worker_dir"

rm -rf .wrangler/state

for file in "$repo_dir/dataset/d1/schema.sql" "$worker_dir/schema.sql" "$repo_dir/dataset/d1/seed.sql"; do
  npx --yes wrangler d1 execute haka --local --file "$file"
done
