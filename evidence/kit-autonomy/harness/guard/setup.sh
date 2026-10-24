#!/usr/bin/env bash
S=${1:?scratch dir}; REPO=$(cd "$(dirname "$0")/../../../.." && pwd)
rm -rf $S/r $S/rf
mkdir -p $S/r/.claude/scripts $S/r/sub $S/rf
git -C $S/r init -q -b main
git -C $S/rf init -q -b feat/x
cp $REPO/.claude/scripts/autonomy.sh $S/r/.claude/scripts/
