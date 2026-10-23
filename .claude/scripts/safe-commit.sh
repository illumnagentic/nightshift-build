#!/usr/bin/env bash
#
# safe-commit.sh — the only permitted way to create a commit in this repository.
#
# Creates a commit whose message is a single title line and nothing else.
# There is no body, therefore there is no field in which an agent signature,
# co-authorship trailer or session link can appear.
#
# Usage:
#   safe-commit.sh "feat(auth): add refresh token rotation"
#   safe-commit.sh --breaking "feat(api): drop v1 response envelope"
#   safe-commit.sh --all "fix(db): close pool on shutdown"      # stages tracked changes
#   safe-commit.sh --dry-run "docs(readme): correct install steps"
#
# Exit codes: 0 ok, 1 bad usage or invalid title, 2 nothing to commit, 3 verification failed.

set -euo pipefail

VALID_TYPES="fix|feat|docs|style|refactor|perf|test|build|ci"
MAX_LEN=72

breaking=0
stage_all=0
dry_run=0
title=""

die() { printf 'safe-commit: %s\n' "$1" >&2; exit "${2:-1}"; }

while [ $# -gt 0 ]; do
  case "$1" in
    --breaking|-b) breaking=1; shift ;;
    --all|-a)      stage_all=1; shift ;;
    --dry-run|-n)  dry_run=1; shift ;;
    -h|--help)
      sed -n '3,20p' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    --) shift; title="${1:-}"; break ;;
    -*) die "unknown option: $1" ;;
    *)  [ -n "$title" ] && die "unexpected extra argument: $1"
        title="$1"; shift ;;
  esac
done

[ -n "$title" ] || die "no commit title given"

# --- Reject anything that is not a single line -------------------------------
# This is the whole point of the script. A newline is how a body gets in.
case "$title" in
  *$'\n'*) die "commit title contains a newline. Commits here are a single line with no body." ;;
esac

# --- Strip any attribution the caller tried to smuggle in --------------------
# Belt and braces: these must never reach a commit message.
case "$title" in
  *Co-Authored-By:*|*Co-authored-by:*|*"Generated with"*|*claude.ai/code*|*Claude-Session:*)
    die "commit title contains an attribution trailer. Signatures are not permitted in commits." ;;
esac

# --- Validate the format -----------------------------------------------------
if ! printf '%s' "$title" | grep -Eq "^(${VALID_TYPES})(\([a-z0-9._/-]+\))?!?: .+$"; then
  die "title must be 'type(scope): message' with type one of: ${VALID_TYPES//|/, }
  got: ${title}"
fi

# Apply --breaking by inserting '!' before the colon, if not already present.
if [ "$breaking" -eq 1 ] && ! printf '%s' "$title" | grep -q '!: '; then
  title="$(printf '%s' "$title" | sed -E "s/^((${VALID_TYPES})(\([a-z0-9._/-]+\))?):/\1!:/")"
fi

len=${#title}
[ "$len" -le "$MAX_LEN" ] || die "title is ${len} characters, limit is ${MAX_LEN}: ${title}"

subject_msg="${title#*: }"
case "$subject_msg" in
  *.) die "title must not end with a full stop" ;;
esac
# LC_ALL=C is required: under a UTF-8 locale, bracket ranges collate as aAbBcC...,
# so [A-Z] matches lowercase b-z and rejects nearly every valid title.
if printf '%s' "$subject_msg" | LC_ALL=C grep -q '^[A-Z]'; then
  die "title message must be lowercase: ${subject_msg}"
fi

# --- Repo checks -------------------------------------------------------------
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "not inside a git repository"

if [ "$stage_all" -eq 1 ]; then
  git add -u
fi

if git diff --cached --quiet; then
  if [ -n "$(git status --porcelain)" ]; then
    die "nothing staged. Stage the files you mean to commit, or pass --all for tracked changes." 2
  fi
  die "nothing to commit — working tree is clean" 2
fi

if [ "$dry_run" -eq 1 ]; then
  printf 'would commit: %s\n' "$title"
  printf '\nstaged files:\n'
  git diff --cached --name-status
  exit 0
fi

# --- Commit ------------------------------------------------------------------
# --cleanup=strip removes comment lines and trailing whitespace.
# No -F, no heredoc, no editor: there is nowhere for a body to come from.
# SAFE_COMMIT_TOKEN tells the repository's pre-commit guard that this commit came
# through the sanctioned route. Nothing else may set it.
SAFE_COMMIT_TOKEN=1 git commit --cleanup=strip -m "$title"

# --- Verify what actually landed --------------------------------------------
# A prepare-commit-msg hook or a commit.template can still append content after the
# message is handed to git. If anything beyond the title survived, rewrite it away.
#
# Note: --no-verify does NOT bypass prepare-commit-msg, so the rewrite points
# core.hooksPath at an empty directory. Hooks ran normally on the real commit above;
# this only disables them for the message-only amend that strips injected content.
trailing_blanks_stripped() { sed -e :a -e '/^[[:space:]]*$/{$d;N;ba' -e '}'; }

actual="$(git log -1 --pretty=%B | trailing_blanks_stripped)"
if [ "$actual" != "$title" ]; then
  printf 'safe-commit: commit message was modified after creation (commit template or prepare-commit-msg hook), rewriting to title only\n' >&2
  empty_hooks="$(mktemp -d)"
  SAFE_COMMIT_TOKEN=1 git -c core.hooksPath="$empty_hooks" commit --amend --cleanup=strip --no-verify -m "$title" >/dev/null
  rmdir "$empty_hooks" 2>/dev/null || true
  recheck="$(git log -1 --pretty=%B | trailing_blanks_stripped)"
  [ "$recheck" = "$title" ] || die "could not enforce title-only commit message. Check for a commit template or prepare-commit-msg hook." 3
fi

printf 'committed: %s\n' "$(git log -1 --pretty='%h %s')"
