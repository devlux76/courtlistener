# Bulk Data Import Process Plan

## Overview
This document outlines the comprehensive process for performing a bulk data import into the PostgreSQL database for the CourtListener project. The process involves fetching data from S3 and importing it into the PostgreSQL database using Docker containers.

## Recent Changes and Improvements

### Enhanced Bulk Data Fetching
The `fetch_bulk_data.py` script has been enhanced with the following improvements:

1. **Size-Based File Ordering**: Files are now sorted by size (largest to smallest) before downloading
2. **Ordered Parallel Downloads**: Files are downloaded in parallel but extracted in size order
3. **Improved Disk Space Management**: Better disk space checking and management to prevent disk from filling up

### Key Implementation Details

#### File Size Ordering
- Modified `get_latest_files()` to fetch file sizes via HEAD requests
- Added sorting function to order files by size (descending)
- Files are processed in this order to ensure largest files are handled first

#### Parallel Downloads with Ordered Extraction
- Implemented a priority queue system for download management
- Files are downloaded in parallel for efficiency
- Extraction happens in strict size order using a separate queue
- Atomic operations are preserved to prevent data corruption

#### Disk Space Management
- Added disk space checking before starting downloads
- Implemented periodic disk space monitoring during downloads
- Added cleanup mechanism for failed downloads
- System pauses downloads if disk space gets too low

## Step-by-Step Execution

### 1. Pre-Import Preparation
- Verify sufficient disk space in the `/srv/bulk-data` directory (minimum 400GB recommended)
- Clean up any old files if needed

### 2. Data Fetching
- Run the fetch process in a container with `/srv/bulk-data` mounted:
  ```bash
  # Use the same image as step 3 for consistency:
  docker compose run --rm cl-bulk-data /workspace/entrypoint-fetch.sh
  ```
- This downloads and extracts files in size order while managing disk space

---
**IMPORTANT FINDING (2025-07-30):**
Running `docker compose run` for the import operation will start all dependent services, even if they were previously stopped. This can unintentionally restart every service, defeating the purpose of stopping non-essential containers. To avoid this, ensure all non-essential services are stopped again after running the import, or consider using `docker compose stop` for all services except the database and bulk import container before and after the import step.

**Action Required:** Update this plan as you discover issues during execution to prevent repeated mistakes.
---
### 3. Data Import
- Stop non-essential containers:
  ```bash
  cd docker/courtlistener
  docker compose stop cl-django cl-celery cl-webpack cl-tailwind-reload cl-selenium cl-webhook-sentry cl-es
  ```
- Run the import operation (using the same image and entrypoint style as step 2):
  ```bash
  docker compose run --rm cl-bulk-data /workspace/entrypoint-import.sh --db-host cl-postgresql --db-user postgres --db-password postgres
  ```

### 4. Post-Import Verification
- Verify data was imported correctly by checking PostgreSQL
- Restart stopped containers

## Pseudocode for Key Components

### Modified get_latest_files() function
```python
def get_latest_files_with_sizes(links):
    """
    Given a list of links, finds the latest file for each base name and gets their sizes.
    Returns list of (filename, url, size) tuples sorted by size (descending).
    """
    file_map = {}
    for link in links:
        fname = link.split('/')[-1]
        if not fname or fname.endswith('.delta'):
            continue
        base = re.sub(r'-\d{4}-\d{2}-\d{2}', '', fname)

        # Get file size via HEAD request
        try:
            head = requests.head(link, timeout=30)
            size = int(head.headers.get("Content-Length", 0))
        except:
            size = 0

        if base not in file_map or fname > file_map[base][0]:
            file_map[base] = (fname, link, size)

    # Sort by size (descending)
    return sorted(file_map.values(), key=lambda x: x[2], reverse=True)
```

### Download Manager with Ordered Extraction
```python
class DownloadManager:
    def __init__(self, files, outdir, max_workers=4):
        self.files = files
        self.outdir = outdir
        self.max_workers = max_workers
        self.download_queue = []
        self.extraction_queue = []
        self.active_downloads = {}
        self.completed_downloads = set()

    def start(self):
        # Initialize queues
        self.extraction_queue = self.files.copy()

        # Start download workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit initial download tasks
            for i in range(min(self.max_workers, len(self.files))):
                self._submit_next_download(executor)

    def _submit_next_download(self, executor):
        if not self.extraction_queue:
            return

        # Get next file to download (already in size order)
        fname, url, size = self.extraction_queue.pop(0)
        self.active_downloads[fname] = executor.submit(self._download_file, fname, url, size)

    def _download_file(self, fname, url, size):
        # Download logic with progress tracking
        # On completion, add to completed downloads
        self.completed_downloads.add(fname)
        return fname, url, size

    def process_completed_downloads(self):
        # Process downloads in order
        while self.extraction_queue and self.extraction_queue[0][0] in self.completed_downloads:
            fname, url, size = self.extraction_queue.pop(0)
            self._extract_file(fname)

    def _extract_file(self, fname):
        # Extraction logic with atomic operations
        pass
```

### Disk Space Management
```python
def check_disk_space(directory, required_space):
    """Check if there's enough disk space available."""
    statvfs = os.statvfs(directory)
    available_space = statvfs.f_frsize * statvfs.f_bavail
    return available_space >= required_space

def get_available_disk_space(directory):
    """Get available disk space in bytes."""
    statvfs = os.statvfs(directory)
    return statvfs.f_frsize * statvfs.f_bavail
```

## Risks and Challenges

1. **Race Conditions**: Careful synchronization is needed between download and extraction threads
2. **Disk Space Management**: Need to handle low disk space situations gracefully
3. **Network Issues**: Robust retry logic is essential for handling network interruptions
4. **Memory Usage**: Large file lists could consume significant memory
5. **File Size Determination**: Some files might not report size correctly

## Monitoring and Error Handling

- Monitor container logs for errors
- Check disk space usage in `/srv/bulk-data` directory
- Verify PostgreSQL connection and performance
- Review import script logs and database state

## Troubleshooting

- **Image/Tag Mismatch**: Ensure both step 2 and step 3 use the same image (`cl-bulk-data` from Compose). If you change the Dockerfile or scripts, always rebuild with:
  ```bash
  cd docker/courtlistener
  docker compose build cl-bulk-data
  ```
- **Architecture Issues**: If running on non-amd64 hardware, adjust the Dockerfile base image to match your architecture (e.g., use an ARM-compatible Python image).
- **Build Context**: The Compose build context for `cl-bulk-data` is the project root. The Dockerfile is at `docker/bulk-data/Dockerfile`.
- **Disk Space Issues**: Clean up old files or increase disk allocation
- **Container Failures**: Check logs and restart containers
- **Import Errors**: Review import script logs and database state