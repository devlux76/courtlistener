"""
Bulk Data Fetcher Script

Downloads and extracts the latest bulk data files from the S3 bucket.
Features:
- Multithreaded downloads
- Robust error handling and retry logic
- File size validation before and after download
- Progress tracking
- Atomic file operations to prevent corruption
- No import functionality (download/extract only)
"""

"""
Bulk Data Fetcher Script

Downloads and extracts the latest bulk data files from the S3 bucket.

Features:
- Multithreaded downloads
- Robust error handling and retry logic
- File size validation before and after download
- Progress tracking
- Atomic file operations to prevent corruption
- No import functionality (download/extract only)
"""

import sys
import os
import re
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests
import bz2
import time
import tempfile
import shutil

URL = "https://com-courtlistener-storage.s3-us-west-2.amazonaws.com/list.html?prefix=bulk-data/"

def get_links():
    """
    Uses Selenium to fetch all bulk-data file links from the S3 bucket listing page.

    Returns:
        list of str: URLs to bulk-data files.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(URL)
    links = [a.get_attribute('href') for a in driver.find_elements('xpath', '//a[contains(@href, "bulk-data/")]')]
    driver.quit()
    return links

def get_latest_files(links):
    """
    Given a list of links, finds the latest file for each base name (ignoring .delta files).

    Args:
        links (list of str): URLs to bulk-data files.

    Returns:
        list of (str, str): Tuples of (filename, url) for latest files.
    """
    file_map = {}
    for link in links:
        fname = link.split('/')[-1]
        if not fname or fname.endswith('.delta'):
            continue
        base = re.sub(r'-\d{4}-\d{2}-\d{2}', '', fname)
        if base not in file_map or fname > file_map[base][0]:
            file_map[base] = (fname, link)
    return list(file_map.values())

import time
import tempfile
import shutil

def download_and_extract(item, outdir, max_retries=5):
    """
    Downloads a file from the given URL with retries, validates file size, shows progress,
    writes atomically, and extracts if .bz2.
    Args:
        item (tuple): (filename, url)
        outdir (str): Output directory
        max_retries (int): Number of download attempts before giving up
    """
    fname, url = item
    local = os.path.join(outdir, fname)
    target_uncompressed = local.replace('.bz2', '')
    target_csv = local.replace('.bz2', '.csv')
    if os.path.exists(target_uncompressed) or os.path.exists(target_csv):
        print(f"Skipping {fname}, already exists.")
        return

    attempt = 0
    while attempt < max_retries:
        print(f"Downloading {fname} (attempt {attempt + 1}) ...")
        try:
            # HEAD request for file size
            head = requests.head(url, timeout=30)
            head.raise_for_status()
            expected_size = int(head.headers.get("Content-Length", 0))
            if expected_size == 0:
                print(f"Warning: Could not determine file size for {fname}")

            # Download with progress and atomic write
            with tempfile.NamedTemporaryFile(delete=False, dir=outdir) as tmpf:
                tmp_path = tmpf.name
                r = requests.get(url, stream=True, timeout=60)
                r.raise_for_status()
                downloaded = 0
                last_percent = -1
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        tmpf.write(chunk)
                        downloaded += len(chunk)
                        if expected_size:
                            percent = int(downloaded * 100 / expected_size)
                            if percent != last_percent and percent % 10 == 0:
                                print(f"  {percent}% downloaded...", end="\r")
                                last_percent = percent
                tmpf.flush()
            # Validate file size
            actual_size = os.path.getsize(tmp_path)
            if expected_size and actual_size != expected_size:
                raise Exception(f"File size mismatch for {fname}: expected {expected_size}, got {actual_size}")

            # Atomic move
            shutil.move(tmp_path, local)
            print(f"Downloaded {fname} ({actual_size} bytes)")

            # Extraction
            if fname.endswith('.bz2'):
                print(f"Extracting {fname} ...")
                with bz2.open(local, 'rb') as f_in, open(local[:-4], 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
                os.remove(local)
            return
        except Exception as e:
            print(f"Error downloading {fname} (attempt {attempt + 1}): {e}")
            attempt += 1
            if attempt < max_retries:
                wait_time = 2 ** attempt
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"Failed to download {fname} after {max_retries} attempts.")

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Fetch and extract latest bulk data files.")
    parser.add_argument("output_dir", help="Directory to store downloaded files")
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel downloads")
    args = parser.parse_args()

    outdir = os.path.abspath(args.output_dir)
    os.makedirs(outdir, exist_ok=True)
    print(f"Fetching bulk data into {outdir}")

    links = get_links()
    latest_files = get_latest_files(links)
    print(f"Found {len(latest_files)} files to download.")

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(download_and_extract, item, outdir) for item in latest_files]
        for future in concurrent.futures.as_completed(futures):
            pass

    print("Bulk data fetch complete.")

if __name__ == "__main__":
    main()