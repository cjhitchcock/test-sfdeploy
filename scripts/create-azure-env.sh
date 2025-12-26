#!/usr/bin/env bash
# create-azure-env.sh
# Usage: ENV=dev ./scripts/create-azure-env.sh
# This will:
#  - create an AAD app registration (gitops-ci-<env>)
#  - create a service principal
#  - add a federated identity credential scoped to the repo+environment
#  - create a Key Vault (kv-<env>) and set policy to allow the SP to get/list secrets
#  - add the SNOWFLAKE_PRIVATE_KEY_BASE64 secret to Key Vault
#
# Pre-requisites:
#  - az CLI installed and logged in (az login)
#  - You must have permission to create app registrations and Key Vault policies
#
# IMPORTANT: replace the placeholders below: YOUR_RG, YOUR_LOCATION, REPO_OWNER, REPO_NAME

set -euo pipefail

ENV="${ENV:-dev}"         # dev | qa | prod
RG="${AZ_RG:-YOUR_RG}"    # Azure resource group
LOCATION="${AZ_LOCATION:-YOUR_LOCATION}"  # e.g. eastus
REPO_OWNER="${REPO_OWNER:-cjhitchcock}"
REPO_NAME="${REPO_NAME:-snowflake-ExcellentData}"

if [[ -z "$ENV" ]]; then
  echo "Set ENV=dev|qa|prod and run this script."
  exit 1
fi

APP_DISPLAY="gitops-ci-${ENV}"
APP_IDENTIFIER="api://gitops-ci-${ENV}"
KV_NAME="kv-${ENV}"
SECRET_NAME="SNOWFLAKE_PRIVATE_KEY_BASE64"

echo "Creating app registration: ${APP_DISPLAY}"
app_json=$(az ad app create \
  --display-name "${APP_DISPLAY}" \
  --identifier-uris "${APP_IDENTIFIER}" \
  --query "{appId:appId,id:id}" -o json)
appId=$(echo "$app_json" | jq -r '.appId')
appObjectId=$(echo "$app_json" | jq -r '.id')

echo "App created. appId=${appId} objectId=${appObjectId}"

# Create service principal
echo "Creating service principal for appId ${appId}"
az ad sp create --id "${appId}" >/dev/null

# Create federated identity credential via Microsoft Graph (az rest)
# Subject limits the token to runs from the repository AND the environment
SUBJECT="repo:${REPO_OWNER}/${REPO_NAME}:environment:${ENV}"
FED_NAME="github-actions-${ENV}"

echo "Adding federated credential subject='${SUBJECT}'"
az rest --method POST \
  --uri "https://graph.microsoft.com/v1.0/applications/${appObjectId}/federatedIdentityCredentials" \
  --headers "Content-Type=application/json" \
  --body "{
    \"name\": \"${FED_NAME}\",
    \"issuer\": \"https://token.actions.githubusercontent.com\",
    \"subject\": \"${SUBJECT}\",
    \"description\": \"Federated credential for GitHub Actions (repo:${REPO_OWNER}/${REPO_NAME}, env:${ENV})\",
    \"audiences\": [\"api://AzureADTokenExchange\"]
  }"

echo "Federated credential added."

# Create Key Vault
echo "Creating Key Vault: ${KV_NAME} in resource group ${RG} (location ${LOCATION})"
az keyvault create --name "${KV_NAME}" --resource-group "${RG}" --location "${LOCATION}" >/dev/null

# Grant the app (by client id) get/list secret permissions
echo "Setting Key Vault access policy for appId ${appId}"
az keyvault set-policy --name "${KV_NAME}" --spn "${appId}" --secret-permissions get list >/dev/null

echo "Key Vault policy set."

# Read private key base64 file (must exist locally)
if [[ ! -f "rsa_key_pkcs8.pem.base64" ]]; then
  echo "ERROR: rsa_key_pkcs8.pem.base64 not found in current directory. Generate key and create this file first."
  exit 2
fi

echo "Uploading SNOWFLAKE_PRIVATE_KEY_BASE64 to Key Vault ${KV_NAME}"
az keyvault secret set --vault-name "${KV_NAME}" --name "${SECRET_NAME}" \
  --value "$(cat rsa_key_pkcs8.pem.base64)" >/dev/null

echo "Secret uploaded to Key Vault."

echo "DONE. App client-id (appId): ${appId}"
echo "Store this client-id in GitHub as AZURE_CLIENT_ID_${ENV^^} (optional). Tenant id is:"
az account show --query tenantId -o tsv

echo ""
echo "Next steps:"
echo " - In GitHub, set repository secret AZURE_CLIENT_ID_${ENV^^} to the above appId (optional)."
echo " - Configure GitHub Environment '${ENV}' (repo Settings -> Environments) and set required approvers for production."
echo " - Create Snowflake user and set RSA_PUBLIC_KEY with the rsa_key.pub content for this environment."