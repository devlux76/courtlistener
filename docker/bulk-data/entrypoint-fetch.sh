#!/bin/bash
set -e

# Entrypoint for bulk data fetch operation
exec python fetch_bulk_data.py "$@"