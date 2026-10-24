S=$(dirname "$0"); cd "$S"; W=$(mktemp -d); export PATH="$PWD/bin:$PATH" GIT_FIX="$PWD/fix" GH_JSON="$W/pr.json" GH_LOG="$W/gh.log"
P=$PWD/../../../../.claude/scripts/safe-merge.sh
case_() { # name branch state base title files args
  python3 - "$2" "$3" "$4" "$5" "$6" > "$GH_JSON" <<'P'
import json,sys
b,s,base,t,f=sys.argv[1:]
print(json.dumps({"state":s,"baseRefName":base,"headRefName":b,"headRefOid":b,"title":t,"files":[{"path":x} for x in f.split(",")]}))
P
  out=$(bash $P 5 ${7:-} 2>&1); ec=$?
  printf '| %s | `safe-merge.sh 5 %s` | %s | %s |\n' "$1" "${7:-}" "$ec" "$(printf '%s' "$out" | head -1)"
}
OK="src/a.txt,lib/x/y.py,t/run.sh,docs/plan.md,.claude/progress/p.md"
case_ "not open" good MERGED main "feat(kit): add x" $OK --check-only
case_ "base not main" good OPEN develop "feat(kit): add x" $OK --check-only
case_ "bad title (no type)" good OPEN main "Add x" $OK --check-only
case_ "bad title (uppercase)" good OPEN main "feat(kit): Add x" $OK --check-only
case_ "bad title (full stop)" good OPEN main "feat(kit): add x." $OK --check-only
case_ "bad title (73 chars)" good OPEN main "feat(kit): $(printf 'a%.0s' $(seq 62))" $OK --check-only
case_ "no progress file" noprog OPEN main "feat(kit): add x" $OK --check-only
case_ "two progress files" dup OPEN main "feat(kit): add x" $OK --check-only
case_ "unticked PLAN box" unticked OPEN main "feat(kit): add x" $OK --check-only
case_ "no QA-GATE PASS" nopass OPEN main "feat(kit): add x" $OK --check-only
case_ "PASS WITH FINDINGS" findings OPEN main "feat(kit): add x" $OK --check-only
case_ "disallowed file" good OPEN main "feat(kit): add x" "src/a.txt,web/app.ts,lib/ok.py,src/b.txt" --check-only
case_ "all good, check-only" good OPEN main "feat(kit)!: add x" $OK --check-only
case_ "evidence-only path allowed" good OPEN main "feat(kit): add x" "evidence/f/x.md" --check-only
case_ "undeclared evidence path refused" good OPEN main "feat(kit): add x" "evidence/f/y.md" --check-only
rm -f "$GH_LOG"
case_ "code commit after PASS" latecode OPEN main "feat(kit): add x" $OK --check-only
case_ "progress-only commits after PASS" progonly OPEN main "feat(kit): add x" $OK --check-only
case_ "PASS commit not found (only PASS WITH FINDINGS in history)" nopasscommit OPEN main "feat(kit): add x" $OK --check-only
case_ "all good, merge" good OPEN main "feat(kit): add x" $OK
echo "merge args received by stub gh: $(cat "$GH_LOG")"
out=$(bash $P abc 2>&1); ec=$?; printf '| bad pr number | `safe-merge.sh abc` | %s | %s |\n' "$ec" "$(echo "$out"|head -1)"
out=$(bash $P 5 --nope 2>&1); ec=$?; printf '| unknown option | `safe-merge.sh 5 --nope` | %s | %s |\n' "$ec" "$(echo "$out"|head -1)"
