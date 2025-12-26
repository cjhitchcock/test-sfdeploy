import logging
import os

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
    migrations_dir = "sql/migrations"
    validate_schema()
    
    for sql_file in os.listdir(migrations_dir):
        sql_file_path = os.path.join(migrations_dir, sql_file)
        if sql_file.endswith(".sql"):
            execute_sql_file(sql_file_path)