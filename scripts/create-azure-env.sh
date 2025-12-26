#!/bin/bash

# Variables
set -euo pipefail
az keyvault secret set --vault-name "$KEY_VAULT_NAME" --name "SF_TEST_USER" --value "$SNOWFLAKE_TEST_USER"
az keyvault secret set --vault-name "$KEY_VAULT_NAME" --name "SF_TEST_PASSWORD" --value "$SNOWFLAKE_TEST_PASSWORD"
az keyvault secret set --vault-name "$KEY_VAULT_NAME" --name "SNOWFLAKE_PRIVATE_KEY" --value "$SNOWFLAKE_PRIVATE_KEY"
az keyvault secret set --vault-name "$KEY_VAULT_NAME" --name "SNOWFLAKE_PRIVATE_KEY_PASSPHRASE" --value "$SNOWFLAKE_PRIVATE_KEY_PASSPHRASE"
