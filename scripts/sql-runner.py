#!/usr/bin/env python3
"""
Simple SQL runner for Snowflake migrations.
- Executes all .sql files in a directory in lexicographic order.
- Uses snowflake-connector-python and environment variables for connection info.
"""
import os
import sys
import glob
import snowflake.connector
from pathlib import Path


def get_conn():
    account = os.getenv("SNOWFLAKE_ACCOUNT")
    user = os.getenv("SNOWFLAKE_USER")
    pwd = os.getenv("SNOWFLAKE_PASSWORD")
    role = os.getenv("SNOWFLAKE_ROLE")
    warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
    database = os.getenv("SNOWFLAKE_DATABASE")
    schema = os.getenv("SNOWFLAKE_SCHEMA")

    if not account or not user or not pwd:
        print("Missing connection environment variables (SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD).")
        sys.exit(1)

    conn_kwargs = {
        'account': account,
        'user': user,
        'password': pwd,
        'role': role,
        'warehouse': warehouse,
        'database': database,
        'schema': schema,
    }

    # Remove keys where value is None to let connector use defaults
    conn_kwargs = {k:v for k,v in conn_kwargs.items() if v}
    return snowflake.connector.connect(**conn_kwargs)


def run_migrations(path):
    path = Path(path)
    files = sorted(path.glob("*.sql"))
    if not files:
        print("No SQL files found in", path)
        return

    conn = get_conn()
    cs = conn.cursor()
    try:
        for f in files:
            print("Running:", f.name)
            sql = f.read_text()
            statements = [s.strip() for s in sql.split(';') if s.strip()]
            for stmt in statements:
                print("Executing statement length:", len(stmt))
                cs.execute(stmt)
        print("Migrations complete.")
    finally:
        cs.close()
        conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: sql-runner.py <migrations-dir>")
        sys.exit(2)
    run_migrations(sys.argv[1])
