#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python -m unittest discover -s tests -t . -v
python examples/tutorial-vault/WORKING/tools/run_probe.py --check
python examples/tutorial-vault/WORKING/tools/run_positive_control.py --check
python -m bvm_lint examples/tutorial-vault --strict
python scripts/check_markdown_links.py .
python scripts/check_public_boundary.py .
python scripts/check_version_parity.py .
python scripts/check_diagnostic_parity.py .
python scripts/check_release_surface.py .
python -m bvm_lint --version

echo "REPOSITORY VERIFY PASS"
