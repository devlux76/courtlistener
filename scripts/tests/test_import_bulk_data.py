import os
import tempfile
import pytest
from unittest import mock
from scripts import import_bulk_data

def test_validate_csv_valid(tmp_path):
    file = tmp_path / "valid.csv"
    file.write_text("col1,col2\n1,2\n")
    assert import_bulk_data.validate_csv(str(file)) is True

def test_validate_csv_invalid(tmp_path):
    file = tmp_path / "invalid.csv"
    file.write_text("")
    assert import_bulk_data.validate_csv(str(file)) is False

def test_validate_sql_valid(tmp_path):
    file = tmp_path / "valid.sql"
    file.write_text("SELECT 1;")
    assert import_bulk_data.validate_sql(str(file)) is True

def test_validate_sql_invalid(tmp_path):
    file = tmp_path / "invalid.sql"
    file.write_text("")
    assert import_bulk_data.validate_sql(str(file)) is False

@mock.patch("psycopg2.connect")
def test_import_sql_file_success(mock_connect, tmp_path):
    file = tmp_path / "test.sql"
    file.write_text("SELECT 1;")
    mock_conn = mock.Mock()
    mock_cursor = mock.Mock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connect.return_value = mock_conn
    import_bulk_data.import_sql_file(mock_conn, str(file))
    mock_cursor.execute.assert_any_call("BEGIN;")
    mock_cursor.execute.assert_any_call("SELECT 1;")
    mock_cursor.execute.assert_any_call("COMMIT;")

@mock.patch("psycopg2.connect")
def test_import_sql_file_error(mock_connect, tmp_path):
    file = tmp_path / "test.sql"
    file.write_text("SELECT 1;")
    mock_conn = mock.Mock()
    mock_cursor = mock.Mock()
    mock_cursor.execute.side_effect = [None, Exception("fail"), None]
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connect.return_value = mock_conn
    with pytest.raises(Exception):
        import_bulk_data.import_sql_file(mock_conn, str(file))

@mock.patch("psycopg2.connect")
def test_import_csv_file_success(mock_connect, tmp_path):
    file = tmp_path / "test.csv"
    file.write_text("col1\n1\n")
    mock_conn = mock.Mock()
    mock_cursor = mock.Mock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connect.return_value = mock_conn
    import_bulk_data.import_csv_file(mock_conn, str(file), "test")
    mock_cursor.execute.assert_any_call("BEGIN;")
    mock_cursor.copy_expert.assert_called()
    mock_cursor.execute.assert_any_call("COMMIT;")

@mock.patch("subprocess.run")
def test_run_shell_loader_success(mock_run):
    mock_run.return_value.returncode = 0
    import_bulk_data.run_shell_loader("/tmp", "host", "user", "pw")
    mock_run.assert_called()

@mock.patch("subprocess.run")
def test_run_shell_loader_failure(mock_run):
    mock_run.return_value.returncode = 1
    with pytest.raises(SystemExit):
        import_bulk_data.run_shell_loader("/tmp", "host", "user", "pw")