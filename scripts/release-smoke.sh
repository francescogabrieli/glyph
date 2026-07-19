#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
if [[ -z "${PYTHON_BIN:-}" ]]; then
  if [[ -x "$ROOT/.venv/bin/python" ]]; then
    PYTHON_BIN="$ROOT/.venv/bin/python"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    PYTHON_BIN="python3"
  fi
fi

BUILD_OUTPUT="$(mktemp -d "${TMPDIR:-/tmp}/glyph-build-output.XXXXXX")"
SMOKE_VENV="$(mktemp -d "${TMPDIR:-/tmp}/glyph-smoke-venv.XXXXXX")"

cleanup() {
  rm -rf "$BUILD_OUTPUT" "$SMOKE_VENV"
}
trap cleanup EXIT

"$PYTHON_BIN" -m build --outdir "$BUILD_OUTPUT"
"$PYTHON_BIN" -m venv "$SMOKE_VENV"
source "$SMOKE_VENV/bin/activate"
python -m pip install "$BUILD_OUTPUT"/*.whl

glyph --help
glyph version
glyph doctor
glyph benchmark benchmarks/
glyph compile benchmarks/backend-fastapi/AGENTS.md -o /tmp/backend.glp --strict --min-structured-coverage 80 --min-retained-coverage 100 --max-high-risk-preserved 0
glyph check benchmarks/backend-fastapi/AGENTS.md /tmp/backend.glp --min-structured-coverage 80 --min-retained-coverage 100 --max-high-risk-preserved 0 --min-reduction 20
glyph inspect benchmarks/readme-dev-section/README.md --show-unmapped
glyph select /tmp/backend.glp --task "fix failing tests" --format markdown

if python -c "import mcp.server.fastmcp" >/dev/null 2>&1; then
  glyph mcp --help
else
  echo 'Skipping MCP smoke: install with pip install "glyph-instructions[mcp]".'
fi
