#!/usr/bin/env bash
# Run `source ./env.sh` from the repository root in WSL/Linux.
_cs149_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export PATH="$_cs149_root/.tools/ispc-v1.28.1-linux/bin:$PATH"
if [[ -f "$_cs149_root/.venv/bin/activate" ]]; then
    source "$_cs149_root/.venv/bin/activate"
fi
unset _cs149_root
