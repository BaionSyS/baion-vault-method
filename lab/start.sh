#!/bin/sh
# Vault Lab entry point. Guided run:  lab/start.sh
# CI verification of all fixtures:    lab/start.sh --check
# POSIX sh; Python 3.11+ stdlib only; runs the in-repository checker via
# PYTHONPATH — no install, no network, no writes outside lab/output/.
set -eu

LAB_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(dirname -- "$LAB_DIR")

PYTHON=${PYTHON:-python3}
if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "vault-lab: python3 not found (need Python 3.11+)" >&2
    exit 2
fi
if ! "$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
    echo "vault-lab: Python 3.11+ required, found $("$PYTHON" -V 2>&1)" >&2
    exit 2
fi

PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="$REPO_ROOT/src${PYTHONPATH:+:$PYTHONPATH}" \
    exec "$PYTHON" "$LAB_DIR/tools/lab.py" "$@"
