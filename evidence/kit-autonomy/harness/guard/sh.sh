#!/usr/bin/env bash
S=${1:?scratch dir}; REPO=$(cd "$(dirname "$0")/../../../.." && pwd)
cd $S/r
for a in status on status off status bogus; do
  printf '%s -> ' "$a"; bash .claude/scripts/autonomy.sh $a 2>&1; echo "   exit $?"
done
cd $REPO
test -e .claude/.autonomy && echo "REAL SWITCH EXISTS" || echo "real switch absent"
git check-ignore -v .claude/.autonomy
