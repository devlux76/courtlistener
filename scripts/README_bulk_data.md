# Bulk Data Import/Export Usage

## Export Bulk Data

To export bulk data and upload to S3, use:

```sh
bash scripts/make_bulk_data.sh
```

This script generates CSVs and compressed files, uploads them to S3, and creates a `load-bulk-data-*.sh` script for import.

## Import Bulk Data

To fetch and import the latest bulk data:

```sh
bash scripts/fetch_bulk_data.sh
```

- Downloads the latest `.bz2` or `.csv` files from S3 using a real browser (Selenium).
- Extracts them into the `bulk-data/` directory.
- Sets up environment variables for bulk import by inspecting the running Postgres Docker container in `docker/courtlistener`.
- Writes an env file with the necessary variables for import.

To load the data after fetching:

```sh
source /tmp/tmp_bulk_env_file  # Path is printed by fetch_bulk_data.sh
bash scripts/load-bulk-data-*.sh
```

## Integration

Both scripts are designed to be run inside the Django container context, with access to Docker Compose and the database.

- No changes to entrypoints or Compose files are required.
- Manual invocation is recommended for both export and import.