"""Snowflake SQL Runner: Execute SQL queries and migrations using private key authentication.

This script streamlines the execution of Snowflake SQL queries and migrations, leveraging private key authentication for robust security.
"""

from snowflake.connector import connect
from snowflake.connector.errors import ProgrammingError
import logging

# Initialize the logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("sql_runner")

def get_conn(account: str, user: str, private_key: str):
    """
    Establishes a Snowflake connection using private key authentication.

    Args:
        account (str): Snowflake account.
        user (str): Snowflake username.
        private_key (str): Private key for authentication.

    Returns:
        connection: Snowflake connection object.

    Raises:
        ProgrammingError: For connection-related issues.
        Exception: General exception for other issues.
    """
    try:
        logger.debug(f"Attempting to connect to account: {account} as user: {user}")
        conn = connect(
            account=account,
            user=user,
            private_key=private_key
        )
        logger.debug("Connection established successfully.")
        return conn

    except ProgrammingError as pe:
        logger.error("ProgrammingError occurred while connecting.", exc_info=True)
        logger.error("Please verify the account, user, and private key credentials for Snowflake.")
        raise pe
    except Exception as e:
        logger.error("An unexpected error occurred during Snowflake connection.", exc_info=True)
        raise e

def run_sql_file(connection, sql_filepath):
    """
    Executes a SQL file.

    Args:
        connection: Snowflake connection object.
        sql_filepath (str): Path to the SQL file.

    Returns:
        None
    """
    logger.debug(f"Preparing to execute SQL file: {sql_filepath}")
    try:
        with open(sql_filepath, 'r') as file:
            sql = file.read()

        with connection.cursor() as cursor:
            logger.debug("Executing SQL script...")
            cursor.execute(sql)
            logger.debug("SQL script executed successfully.")
    except Exception as e:
        logger.error("An error occurred while executing the SQL file.", exc_info=True)
        raise e

def run_migrations(connection, migrations):
    """
    Executes a series of SQL migration scripts.

    Args:
        connection: Snowflake connection object.
        migrations (list): List of SQL file paths in migration order.

    Returns:
        None
    """
    logger.debug("Starting migrations...")
    for migration in migrations:
        logger.debug(f"Starting migration file: {migration}")
        try:
            run_sql_file(connection, migration)
            logger.debug(f"Migration {migration} completed successfully.")
        except Exception as e:
            logger.error(f"Migration {migration} failed.", exc_info=True)
            raise e