# Bulk Data Import Process Plan

## Overview
This document outlines the comprehensive process for performing a bulk data import into the PostgreSQL database for the CourtListener project. The process involves fetching data from S3 and importing it into the PostgreSQL database using Docker containers.

## Step-by-Step Execution

# Note on Bulk Data Directory Location

The bulk data directory is now located at `/srv/bulk-data`. For compatibility, a symbolic link from the previous location points to `/srv/bulk-data`. All scripts and processes should reference `/srv/bulk-data` directly or rely on the symlink if needed.

### 1. Pre-Import Preparation
- Verify sufficient disk space in the `/srv/bulk-data` directory after cleaning up any files (total space needed is around 400GB) the process should not fail merely for insufficient diskspace, but it will determine how fast we can go.

### 2. Data Fetching
- **Important:** 
- The fetch process must be run by starting a container with `/srv/bulk-data` mounted from the host, and executing the Python fetch script directly inside that container. However if there is less than 400GB of diskspace start the download with the largest files and bunzip them one at a time.

- Example:
  ```bash
  docker run --rm -v /srv/bulk-data:/srv/bulk-data -w /workspace bulkdata-fetcher /workspace/entrypoint-fetch.sh
  ```
- This will download data from S3 to the `/srv/bulk-data` directory (see note below)

### 3. Data Import
- Stop non-essential containers to free up resources:
  ```bash
  cd docker/courtlistener
  docker compose stop cl-django cl-celery cl-webpack cl-tailwind-reload cl-selenium cl-webhook-sentry cl-es
  ```

  - IMPORTANT: Ensure the PostgreSQL container (cl-postgresql) is running and healthy

- Run the import operation using Docker:
  ```bash
  docker compose run --rm cl-bulk-data bash scripts/import_bulk_data.sh --db-host cl-postgresql --db-user postgres --db-password postgres
  ```
- Monitor logs for progress and errors

### 4. Post-Import Verification
- Verify data was imported correctly by checking PostgreSQL
- Restart stopped containers:
  ```bash
  docker compose up -d cl-django cl-celery cl-webpack cl-tailwind-reload cl-selenium cl-webhook-sentry cl-es
  ```

## Container Management

### Required Containers
- cl-postgresql (PostgreSQL database)
- cl-bulk-data (runs import scripts)

### Containers to Stop During Import
- cl-django (web application)
- cl-celery (task server)
- cl-webpack (frontend build)
- cl-tailwind-reload (CSS reload)
- cl-selenium (browser automation)
- cl-webhook-sentry (error reporting)
- cl-es (Elasticsearch)

## Monitoring and Error Handling
- Monitor container logs for errors
- Check disk space usage in `/srv/bulk-data` directory
- Verify PostgreSQL connection and performance

## Troubleshooting
- **Disk Space Issues**: Free up space or increase disk allocation
- **Container Failures**: Check logs and restart containers
- **Import Errors**: Review import script logs and database state
## Recent Outcomes & Issues

### Successful Fetch and Selenium/Docker Fixes
- Bulk data files were successfully fetched.
- The fetch script and Docker setup were corrected to use Selenium properly.

### Disk Space Exhaustion and File Management Issues
- The process encountered a disk space exhaustion issue after fetching the data.
- Hundreds of temporary files (e.g., `tmpvz6exw3o`, `tmpw99j70kh`) and large files (e.g., `tmpy54yrojd` at 18G) were created in the project root.
- `.csv` files were misplaced in the project root instead of the intended directory.

### Recommendations for Cleanup and Prevention
- **Cleanup**:
  - Manually delete temporary files (`tmp*`) and oversized files from the project root.
  - Move `.csv` files to the intended directory (`./bulk-data` or `/srv/bulk-data`).

- **Prevention**:
  - Modify the script to enforce a default `output_dir` (e.g., `./bulk-data`) if not provided.
  - Add validation in `entrypoint-fetch.sh` to ensure `output_dir` is correctly set.
  - Implement cleanup logic for temporary files in case of script failure or interruption.

These changes will prevent future accumulation of junk files and ensure `.csv` files are stored in the correct directory.