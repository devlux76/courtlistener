## Running Tests

To run the automated tests for `fetch_bulk_data.py` and `import_bulk_data.py`, ensure you have `pytest` installed:

```bash
pip install pytest
```

Then run:

```bash
pytest scripts/tests/
```

The tests use mocking and temporary files, so they do not require real S3, network, or database access.
# Bulk Data Import/Export Guide

## Overview

The bulk data workflow is now separated into two distinct operations: **fetch** and **import**. This allows for more flexible, reliable, and repeatable data management.

- **Fetch**: Downloads the latest bulk data files from S3 and stores them locally.
- **Import**: Loads the fetched data into the database.

Both operations are run inside a Docker container for consistency and isolation.

---

## 1. Fetching Bulk Data

Use [`fetch_bulk_data.sh`](fetch_bulk_data.sh) to download the latest bulk data files.

**Usage:**
```sh
bash scripts/fetch_bulk_data.sh [options]
```

- Options are passed directly to [`fetch_bulk_data.py`](fetch_bulk_data.py).
- Downloads files into the `bulk-data/` directory (must exist at project root).
- Runs inside a Docker container with the necessary dependencies.

**Example:**
```sh
bash scripts/fetch_bulk_data.sh --bucket my-bucket --prefix 2025/
```

---

## 2. Importing Bulk Data

After fetching, use [`import_bulk_data.sh`](import_bulk_data.sh) to load the data into the database.

**Usage:**
```sh
bash scripts/import_bulk_data.sh [options]
```

- Options are passed directly to [`import_bulk_data.py`](import_bulk_data.py).
- Reads from the `bulk-data/` directory.
- Runs inside a Docker container with database access.

**Example:**
```sh
bash scripts/import_bulk_data.sh --db-host db --db-user postgres
```

---

## 3. Docker Container Configuration

Both scripts use Docker to ensure a consistent environment:

- **Image**: `python:3` (or see [`docker/bulk-data/Dockerfile`](../docker/bulk-data/Dockerfile) for custom builds)
- **Volumes**:
  - `bulk-data/` (host) → `/app/bulk-data` (container): persists downloaded data
  - `scripts/` (host) → `/app/scripts` (container): provides scripts
- **Working Directory**: `/app`
- **Environment Variables**: Can be set for database connection (see Dockerfile for defaults)

You may customize the Docker image or entrypoints as needed.

---

## 4. Troubleshooting

- **bulk-data directory not found**  
  Ensure `bulk-data/` exists at the project root before running either script.

- **Docker permission errors**  
  Make sure your user has permission to run Docker and access the project directories.

- **Database connection issues**  
  Check that the database is running and credentials match the environment variables.

- **File not found or access denied**  
  Verify that the required files exist in `bulk-data/` and have correct permissions.

- **Custom arguments**  
  Use `-h` or `--help` with either script to see available options for the underlying Python scripts.

---

## 5. Notes

- Both scripts are intended for manual invocation.
- No changes to Docker Compose or entrypoints are required.
- The workflow is compatible with local development and CI environments.