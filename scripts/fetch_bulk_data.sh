#!/bin/bash
set -e

# Requirements: python3, pip, unzip, bzip2, docker-compose, jq
# This script downloads the latest bulk-data files from S3, extracts them, and sets up env vars for bulk import.

BULK_DATA_DIR="$(dirname "$0")/../bulk-data"
DOCKER_COMPOSE_DIR="$(dirname "$0")/../docker/courtlistener"
PYTHON_SCRIPT="$(mktemp)"
ENV_FILE="$(mktemp)"

mkdir -p "$BULK_DATA_DIR"

cat > "$PYTHON_SCRIPT" <<EOF
import sys, os, re, concurrent.futures
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests, bz2

URL = "https://com-courtlistener-storage.s3-us-west-2.amazonaws.com/list.html?prefix=bulk-data/"
OUTDIR = os.path.abspath(sys.argv[1])

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=chrome_options)
driver.get(URL)
links = [a.get_attribute('href') for a in driver.find_elements('xpath', '//a[contains(@href, "bulk-data/")]')]
driver.quit()

# Find latest version for each file base (ignoring deltas)
file_map = {}
for link in links:
    fname = link.split('/')[-1]
    if not fname or fname.endswith('.delta'): continue
    base = re.sub(r'-\\d{4}-\\d{2}-\\d{2}', '', fname)
    if base not in file_map or fname > file_map[base][0]:
        file_map[base] = (fname, link)

def download_and_extract(item):
    fname, url = item
    local = os.path.join(OUTDIR, fname)
    if os.path.exists(local.replace('.bz2', '')) or os.path.exists(local.replace('.bz2', '.csv')):
        return
    print(f"Downloading {fname} ...")
    r = requests.get(url, stream=True)
    with open(local, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    if fname.endswith('.bz2'):
        print(f"Extracting {fname} ...")
        with bz2.open(local, 'rb') as f_in, open(local[:-4], 'wb') as f_out:
            f_out.write(f_in.read())
        os.remove(local)

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    executor.map(download_and_extract, file_map.values())
EOF

python3 "$PYTHON_SCRIPT" "$BULK_DATA_DIR"
rm "$PYTHON_SCRIPT"

# Set up environment variables for bulk import.
echo "export BULK_DIR=\"$BULK_DATA_DIR\"" > "$ENV_FILE"
echo "export BULK_DB_HOST=\"\${BULK_DB_HOST:-localhost}\"" >> "$ENV_FILE"
echo "export BULK_DB_USER=\"\${BULK_DB_USER:-postgres}\"" >> "$ENV_FILE"
echo "export BULK_DB_PASSWORD=\"\${BULK_DB_PASSWORD:-postgres}\"" >> "$ENV_FILE"

echo "Environment variables for bulk import written to $ENV_FILE"
echo "Debug: Python script executed successfully."
echo "To load bulk data, run:"
echo "  source $ENV_FILE"
echo "  bash scripts/load-bulk-data-*.sh"
echo ""
echo "Set BULK_DB_HOST, BULK_DB_USER, and BULK_DB_PASSWORD as needed for your environment."