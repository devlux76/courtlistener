#!/bin/bash
set -e

# Entrypoint for bulk data import operation
exec python scripts/import_bulk_data.py "$@"