# Snowflake Key Rotation Runbook

## 1. Generate new key pair
Use OpenSSL or another appropriate tool to generate an RSA key pair. Ensure the private key is securely stored and encrypted with a passphrase.

```bash
openssl genrsa -aes256 -out rsa_key.pem 2048
openssl rsa -in rsa_key.pem -pubout -out rsa_key.pub
```

## 2. Stage public key in Snowflake
Upload the public key to Snowflake as a secondary key for seamless rotation:

```sql
ALTER USER gitops_ci_<env> SET RSA_PUBLIC_KEY_2 = '<contents-of-rsa_new.pub>';
```

Rollback guidance for clearing secondary keys if required:

```sql
ALTER USER gitops_ci_<env> UNSET RSA_PUBLIC_KEY_2;
```

## 3. Update Key Vault secret
Update the private key and passphrase in Azure Key Vault. Ensure both are updated atomically:

```bash
az keyvault secret set --vault-name kv-<env> --name SNOWFLAKE_PRIVATE_KEY --file rsa_key.pem
az keyvault secret set --vault-name kv-<env> --name SNOWFLAKE_PRIVATE_KEY_PASSPHRASE --value "<new-passphrase>"
```

## 4. Test pipeline
Trigger the CI/CD pipeline for verification. Ensure both old and new keys are functioning if using secondary key rotation.
Enhanced testing includes automated verification:

```bash
gh run workflow --name "test-migration" --env dev
```

Check the pipeline logs for any authentication errors or warnings.

## 5. Promote new key
Remove the old key from Snowflake and promote the new key to primary:

```sql
ALTER USER gitops_ci_<env> SET RSA_PUBLIC_KEY = '<contents-of-rsa_new.pub>';
ALTER USER gitops_ci_<env> UNSET RSA_PUBLIC_KEY_2;
```

## 6. Rollback Plan
If any issues are encountered, revert back to the old key and document all rollback attempts.
Ensure Azure Key Vault logging is enabled to trace changes:

```bash
az keyvault diagnostic-settings create --name "LogToLogAnalytics" --vault-name kv-<env> --workspace /subscriptions/<sub_id>/resourceGroups/<rg_name>/providers/Microsoft.OperationalInsights/workspaces/<workspace_name>
```

Review Snowflake query history to ensure no unauthorized access has occurred during the rotation process.
