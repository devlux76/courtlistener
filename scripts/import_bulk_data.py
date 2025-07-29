#!/usr/bin/env python3
"""
Bulk Data Import Script

- Handles PostgreSQL connection
- Implements data validation
- Adds transaction management
- Supports both CSV and SQL file formats
- Runs the bulk-data/load-bulk-data script inside the container

Designed to work with files downloaded by fetch_bulk_data.py.
"""

import os
import sys
import glob
import subprocess
import psycopg2
import csv

def validate_csv(file_path):
    """Basic CSV validation: checks if file is readable and has at least a header."""
    try:
        with open(file_path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not header:
                print(f"Validation failed: {file_path} has no header.")
                return False
        return True
    except Exception as e:
        print(f"Validation failed for {file_path}: {e}")
        return False

def validate_sql(file_path):
    """Basic SQL validation: checks if file is readable and not empty."""
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                print(f"Validation failed: {file_path} is empty.")
                return False
        return True
    except Exception as e:
        print(f"Validation failed for {file_path}: {e}")
        return False

def import_sql_file(conn, file_path):
    """Import SQL file inside a transaction."""
    with open(file_path, encoding='utf-8') as f:
        sql = f.read()
    with conn.cursor() as cur:
        try:
            cur.execute("BEGIN;")
            cur.execute(sql)
            cur.execute("COMMIT;")
            print(f"Imported SQL: {file_path}")
        except Exception as e:
            cur.execute("ROLLBACK;")
            print(f"Error importing {file_path}: {e}")
            raise

def import_csv_file(conn, file_path, table_name):
    """Import CSV file using COPY inside a transaction."""
    with open(file_path, encoding='utf-8') as f:
        with conn.cursor() as cur:
            try:
                cur.execute("BEGIN;")
                cur.copy_expert(f"COPY {table_name} FROM STDIN WITH CSV HEADER", f)
                cur.execute("COMMIT;")
                print(f"Imported CSV: {file_path} -> {table_name}")
            except Exception as e:
                cur.execute("ROLLBACK;")
                print(f"Error importing {file_path}: {e}")
                raise

def run_shell_loader(bulk_dir, db_host, db_user, db_password):
    """Run the bulk-data/load-bulk-data shell script with required environment."""
    script_path = os.path.join("bulk-data", "load-bulk-data-2025-07-02.sh")
    env = os.environ.copy()
    env["BULK_DIR"] = bulk_dir
    env["BULK_DB_HOST"] = db_host
    env["BULK_DB_USER"] = db_user
    env["BULK_DB_PASSWORD"] = db_password
    print(f"Running shell loader: {script_path}")
    result = subprocess.run(["bash", script_path], env=env)
    if result.returncode != 0:
        print("Shell loader failed.")
        sys.exit(1)
    print("Shell loader completed successfully.")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Import bulk data into PostgreSQL.")
    parser.add_argument("bulk_dir", help="Directory containing extracted bulk data files")
    parser.add_argument("--db-host", required=True, help="PostgreSQL host")
    parser.add_argument("--db-user", required=True, help="PostgreSQL user")
    parser.add_argument("--db-password", required=True, help="PostgreSQL password")
    parser.add_argument("--db-name", default="courtlistener", help="PostgreSQL database name")
    parser.add_argument("--mode", choices=["shell", "direct"], default="shell",
                        help="Import mode: 'shell' (recommended) or 'direct' (Python)")
    args = parser.parse_args()

    # Validate files
    csv_files = glob.glob(os.path.join(args.bulk_dir, "*.csv"))
    sql_files = glob.glob(os.path.join(args.bulk_dir, "*.sql"))
    all_valid = True

    for f in csv_files:
        if not validate_csv(f):
            all_valid = False
    for f in sql_files:
        if not validate_sql(f):
            all_valid = False

    if not all_valid:
        print("Validation failed. Aborting import.")
        sys.exit(1)

    if args.mode == "shell":
        run_shell_loader(args.bulk_dir, args.db_host, args.db_user, args.db_password)
    else:
        # Direct import using psycopg2
        try:
            conn = psycopg2.connect(
                host=args.db_host,
                user=args.db_user,
                password=args.db_password,
                dbname=args.db_name,
            )
            # Import SQL files first
            for sql_file in sql_files:
                import_sql_file(conn, sql_file)
            # Import CSV files (table name inferred from file name)
            for csv_file in csv_files:
                table_name = os.path.splitext(os.path.basename(csv_file))[0]
                import_csv_file(conn, csv_file, table_name)
            conn.close()
            print("Direct import completed successfully.")
        except Exception as e:
            print(f"Direct import failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()