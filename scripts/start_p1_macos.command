#!/bin/bash
# Use the explicitly installed pilot environment; do not modify it automatically.
set -eu
repo_root="$(cd -- "$(dirname -- "$0")/.." && pwd)"
if [ ! -x "$repo_root/.venv-p1/bin/python" ]; then
  echo "Install the P1 wheel into .venv-p1 first; see docs/P1.md."
  exit 2
fi
exec "$repo_root/.venv-p1/bin/python" -m strd.desktop
