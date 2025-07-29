import os
import tempfile
import pytest
from unittest import mock
from scripts import fetch_bulk_data

@pytest.fixture
def fake_links():
    return [
        "https://bucket/bulk-data/file1-2025-07-01.csv.bz2",
        "https://bucket/bulk-data/file2-2025-07-01.csv.bz2",
        "https://bucket/bulk-data/file1-2025-06-01.csv.bz2",
        "https://bucket/bulk-data/file2-2025-06-01.csv.bz2",
        "https://bucket/bulk-data/file1-2025-07-01.delta"
    ]

def test_get_latest_files(fake_links):
    latest = fetch_bulk_data.get_latest_files(fake_links)
    names = [x[0] for x in latest]
    assert "file1-2025-07-01.csv.bz2" in names
    assert "file2-2025-07-01.csv.bz2" in names
    assert all(not n.endswith(".delta") for n in names)

@mock.patch("scripts.fetch_bulk_data.requests.get")
@mock.patch("scripts.fetch_bulk_data.requests.head")
def test_download_and_extract_success(mock_head, mock_get):
    # Setup
    mock_head.return_value.status_code = 200
    mock_head.return_value.headers = {"Content-Length": "10"}
    mock_get.return_value.status_code = 200
    mock_get.return_value.iter_content = lambda chunk_size: [b"12345", b"67890"]
    with tempfile.TemporaryDirectory() as tmpdir:
        item = ("test.csv.bz2", "http://example.com/test.csv.bz2")
        # Patch bz2.open and shutil.copyfileobj to simulate extraction
        with mock.patch("scripts.fetch_bulk_data.bz2.open", mock.mock_open(read_data=b"data")), \
             mock.patch("scripts.fetch_bulk_data.shutil.copyfileobj"), \
             mock.patch("os.remove"):
            fetch_bulk_data.download_and_extract(item, tmpdir)
        # File should be extracted and original bz2 removed (os.remove called)

@mock.patch("scripts.fetch_bulk_data.requests.get")
@mock.patch("scripts.fetch_bulk_data.requests.head")
def test_download_and_extract_file_size_mismatch(mock_head, mock_get):
    mock_head.return_value.status_code = 200
    mock_head.return_value.headers = {"Content-Length": "10"}
    mock_get.return_value.status_code = 200
    mock_get.return_value.iter_content = lambda chunk_size: [b"123"]
    with tempfile.TemporaryDirectory() as tmpdir:
        item = ("bad.csv.bz2", "http://example.com/bad.csv.bz2")
        # Patch to avoid actual extraction
        with mock.patch("scripts.fetch_bulk_data.bz2.open"), \
             mock.patch("scripts.fetch_bulk_data.shutil.copyfileobj"), \
             mock.patch("os.remove"):
            with pytest.raises(Exception):
                fetch_bulk_data.download_and_extract(item, tmpdir, max_retries=1)

@mock.patch("scripts.fetch_bulk_data.requests.get")
@mock.patch("scripts.fetch_bulk_data.requests.head")
def test_download_and_extract_network_error(mock_head, mock_get):
    mock_head.side_effect = Exception("Network error")
    with tempfile.TemporaryDirectory() as tmpdir:
        item = ("fail.csv.bz2", "http://example.com/fail.csv.bz2")
        with mock.patch("time.sleep"):
            fetch_bulk_data.download_and_extract(item, tmpdir, max_retries=1)