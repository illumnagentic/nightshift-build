#!/usr/bin/env bash
#
# kit-py.sh — find a working Python 3 for the kit's hooks and scripts. Source it:
#
#   . "$here/kit-py.sh"
#   kit_py -I -c 'print(1)'          # runs Python, output with any CR removed
#   [ "${#KIT_PY[@]}" -gt 0 ]        # true when a working Python 3 was found
#
# Why not just `python3`:
#   - On Windows, `python3` is often the Microsoft Store alias. `command -v` finds it,
#     but running it fails, so a hook that trusted `command -v` would silently stop
#     checking anything. Each candidate here is actually run before it is used.
#   - Python from python.org is `python` or `py -3` on Windows, not `python3`.
#   - Native Windows Python writes CRLF. kit_py strips the CR so that values read
#     back in bash compare equal ("OPEN", not "OPEN\r").
#
# kit_py returns Python's own exit code.

KIT_PY=()
for _kit_py_c in python3 python "py -3"; do
  # shellcheck disable=SC2086  # "py -3" is two words on purpose
  if $_kit_py_c -c 'import sys; sys.exit(sys.version_info < (3, 8))' >/dev/null 2>&1; then
    read -r -a KIT_PY <<< "$_kit_py_c"
    break
  fi
done
unset _kit_py_c

kit_py() {
  [ "${#KIT_PY[@]}" -gt 0 ] || { echo "kit: no working Python 3 found (tried python3, python, py -3)" >&2; return 127; }
  "${KIT_PY[@]}" "$@" | tr -d '\r'
  return "${PIPESTATUS[0]}"
}
