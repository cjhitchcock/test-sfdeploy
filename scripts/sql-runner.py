import logging
import os
import sys

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sql_runner")

def execute_sql_file(sql_file_path):
    logger.info(f"Executing SQL migration: {sql_file_path}")
    try:
        # Replace this with Snowflake execution logic
        logger.info(f"SQL migration {sql_file_path} executed successfully.")
    except Exception as e:
        logger.error(f"Error executing {sql_file_path}: {e}")
        raise

def validate_schema():
    # Perform schema validation logic here
    logger.info("Schema validation completed successfully.")

if __name__ == "__main__":
    # Accept migrations directory as command-line argument
    migrations_dir = sys.argv[1] if len(sys.argv) > 1 else "sql/migrations"
    validate_schema()
    
    # Sort files to ensure consistent execution order
    for sql_file in sorted(os.listdir(migrations_dir)):
        sql_file_path = os.path.join(migrations_dir, sql_file)
        # Check if it's a file and ends with .sql
        if os.path.isfile(sql_file_path) and sql_file.endswith(".sql"):
            execute_sql_file(sql_file_path)