#!/bin/bash

# Variables - These must be set as environment variables before running this script:
# - KEY_VAULT_NAME: The name of the Azure Key Vault
# - SNOWFLAKE_TEST_USER: The Snowflake test user
# - SNOWFLAKE_TEST_PASSWORD: The Snowflake test password
# - SNOWFLAKE_PRIVATE_KEY: The Snowflake private key (base64 encoded)
# - SNOWFLAKE_PRIVATE_KEY_PASSPHRASE: The Snowflake private key passphrase

set -euo pipefail

# Suppress secret values in output by using --query to only show the secret ID
az keyvault secret set --vault-name "$KEY_VAULT_NAME" --name "SF_TEST_USER" --value "$SNOWFLAKE_TEST_USER" --query "id" -o tsv
az keyvault secret set --vault-name "$KEY_VAULT_NAME" --name "SF_TEST_PASSWORD" --value "$SNOWFLAKE_TEST_PASSWORD" --query "id" -o tsv
az keyvault secret set --vault-name "$KEY_VAULT_NAME" --name "SNOWFLAKE_PRIVATE_KEY_BASE64" --value "$SNOWFLAKE_PRIVATE_KEY" --query "id" -o tsv
az keyvault secret set --vault-name "$KEY_VAULT_NAME" --name "SNOWFLAKE_PRIVATE_KEY_PASSPHRASE" --value "$SNOWFLAKE_PRIVATE_KEY_PASSPHRASE" --query "id" -o tsv
