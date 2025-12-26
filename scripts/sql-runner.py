#!/usr/bin/env python3
"""
sql-runner.py
- Connects to Snowflake using either private-key (preferred) or password auth.
- Expects environment variables:
  - SNOWFLAKE_ACCOUNT
  - SNOWFLAKE_USER
  - SNOWFLAKE_ROLE (optional)
  - SNOWFLAKE_WAREHOUSE (optional)
  - SNOWFLAKE_DATABASE (optional)
  - SNOWFLAKE_SCHEMA (optional)
  - SNOWFLAKE_PRIVATE_KEY_BASE64 (base64 of PKCS#8 PEM) OR SNOWFLAKE_PASSWORD
  - SNOWFLAKE_PRIVATE_KEY_PASSPHRASE (optional)
Usage:
  python scripts/sql-runner.py sql/migrations
"""

from pathlib import Path
import os
import sys
import base64
import logging

# Minimal logging config (do not log secrets)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

try:
    import snowflake.connector
except Exception as e:
    logger.error("snowflake-connector-python is required. Install with pip.")
    raise

# cryptography is required for private key loading
try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend
except Exception:
    logger.error("cryptography is required for private-key auth. Install with pip.")
    raise


def _conn_kwargs_from_env():
    """
    Gather non-secret connection kwargs from environment; exclude None values.
    """
    env = os.environ
    kw = {
        "account": env.get("SNOWFLAKE_ACCOUNT"),
        "user": env.get("SNOWFLAKE_USER"),
        "role": env.get("SNOWFLAKE_ROLE"),
        "warehouse": env.get("SNOWFLAKE_WAREHOUSE"),
        "database": env.get("SNOWFLAKE_DATABASE"),
        "schema": env.get("SNOWFLAKE_SCHEMA"),
    }
    # Remove unset
    return {k: v for k, v in kw.items() if v}


def _connect_with_private_key(pk_b64: str, pk_passphrase: str = None):
    """
    Load a base64-encoded PKCS#8 PEM private key and connect using snowflake.connector.
    Returns a Snowflake connection object.
    """
    try:
        pk_bytes = base64.b64decode(pk_b64)
    except Exception as e:
        logger.error("Failed to base64-decode private key: %s", e)
        raise

    try:
        private_key = serialization.load_pem_private_key(
            pk_bytes,
            password=(pk_passphrase.encode() if pk_passphrase else None),
            backend=default_backend(),
        )
    except Exception as e:
        logger.error("Failed to load private key: %s", e)
        raise

    # Export private key bytes in PKCS8 PEM (unencrypted) for the connector
    try:
        pk_for_connector = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    except Exception as e:
        logger.error("Failed to serialize private key for connector: %s", e)
        raise

    conn_kwargs = _conn_kwargs_from_env()
    conn_kwargs["private_key"] = pk_for_connector
    # Do not include password
    logger.info("Connecting to Snowflake using private-key auth (user=%s)", conn_kwargs.get("user"))
    return snowflake.connector.connect(**conn_kwargs)


def _connect_with_password(password: str):
    conn_kwargs = _conn_kwargs_from_env()
    conn_kwargs["password"] = password
    logger.info("Connecting to Snowflake using password auth (user=%s)", conn_kwargs.get("user"))
    return snowflake.connector.connect(**conn_kwargs)


def get_conn():
    """
    Choose auth method: private-key if SNOWFLAKE_PRIVATE_KEY_BASE64 is present; otherwise password.
    Raises SystemExit on missing configuration.
    """
    env = os.environ
    account = env.get("SNOWFLAKE_ACCOUNT")
    user = env.get("SNOWFLAKE_USER")
    if not account or not user:
        logger.error("Missing SNOWFLAKE_ACCOUNT or SNOWFLAKE_USER environment variables.")
        raise SystemExit(1)

    pk_b64 = env.get("SNOWFLAKE_PRIVATE_KEY_BASE64")
    pk_pass = env.get("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE")
    pwd = env.get("SNOWFLAKE_PASSWORD")

    if pk_b64:
        try:
            return _connect_with_private_key(pk_b64, pk_pass)
        except Exception:
            logger.exception("Private-key authentication failed.")
            raise

    if pwd:
        try:
            return _connect_with_password(pwd)
        except Exception:
            logger.exception("Password authentication failed.")
            raise

    logger.error("No SNOWFLAKE_PRIVATE_KEY_BASE64 or SNOWFLAKE_PASSWORD found in environment.")
    raise SystemExit(1)


def run_sql_file(conn, sql_path: Path):
    sql_text = sql_path.read_text(encoding="utf-8")
    # Simple split on semicolon; adapt if you store complex statements
    statements = [s.strip() for s in sql_text.split(";") if s.strip()]
    cursor = conn.cursor()
    try:
        for stmt in statements:
            logger.info("Executing statement from %s: %.60s", sql_path.name, stmt.replace("\n", " ")[:60])
            cursor.execute(stmt)
        conn.commit()
    finally:
        cursor.close()


def run_migrations(path):
    p = Path(path)
    if not p.exists():
        logger.error("Migration path not found: %s", path)
        raise SystemExit(1)
    # Run SQL files in alphabetical order
    files = sorted([f for f in p.glob("*.sql")])
    if not files:
        logger.info("No migrations found in %s", path)
        return
    conn = get_conn()
    try:
        for f in files:
            run_sql_file(conn, f)
    finally:
        conn.close()


def main(argv):
    if len(argv) < 2:
        print("Usage: python scripts/sql-runner.py <migrations-dir>")
        raise SystemExit(2)
    run_migrations(argv[1])


if __name__ == "__main__":
    main(sys.argv)