#!/usr/bin/env bash
set -e

# Dynamically resolve project root (one directory up from scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"

# Verify that the virtual environment exists in the project root
if [ ! -f "$VENV_PYTHON" ]; then
    echo "[ERROR] Virtual environment (.venv) not found at $PROJECT_ROOT/.venv!"
    echo "Please run the setup script first (e.g., ./scripts/setup.sh)."
    exit 1
fi

# Switch working directory to project root so relative paths work properly
cd "$PROJECT_ROOT"

# Run the main orchestrator using the virtual environment's python
exec "$VENV_PYTHON" main.py "$@"