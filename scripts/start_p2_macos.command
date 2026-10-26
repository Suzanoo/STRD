#!/bin/bash
# Use the explicitly installed pilot environment; do not modify it automatically.
set -eu
repo_root="$(cd -- "$(dirname -- "$0")/.." && pwd)"
if [ ! -x "$repo_root/.venv-p2/bin/python" ]; then
  echo "Install the P2 wheel into .venv-p2 first; see docs/P2.md."
  exit 2
fi
exec "$repo_root/.venv-p2/bin/python" -m strd.desktop
