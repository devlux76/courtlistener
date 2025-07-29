#!/bin/bash

set -e

usage() {
    echo "Usage: $0 [options]"
    echo "Runs import_bulk_data.py inside the Docker container."
    echo ""
    echo "Options are passed directly to import_bulk_data.py."
    echo ""
    echo "Example:"
    echo "  $0 --arg1 value1 --arg2 value2"
    exit 1
}

if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    usage
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BULK_DATA_DIR="$PROJECT_ROOT/bulk-data"

if [[ ! -d "$BULK_DATA_DIR" ]]; then
    echo "Error: bulk-data directory not found at $BULK_DATA_DIR"
    exit 2
fi

docker run --rm \
    -v "$BULK_DATA_DIR":/app/bulk-data \
    -v "$SCRIPT_DIR":/app/scripts \
    -w /app \
    python:3 \
    python scripts/import_bulk_data.py "$@"

EXIT_CODE=$?
if [[ $EXIT_CODE -ne 0 ]]; then
    echo "import_bulk_data.py failed with exit code $EXIT_CODE"
    exit $EXIT_CODE
fi