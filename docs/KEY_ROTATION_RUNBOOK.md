# Key Rotation Runbook — Snowflake CI private keys (per-environment)

Purpose
- Document the safe procedure to rotate the RSA private/public key pair used by GitHub Actions -> Azure Key Vault -> Snowflake CI users.
- This is the per-environment process. Repeat for dev, qa, prod.

Assumptions
- Environment name = <env> (dev/qa/prod)
- Snowflake CI user = gitops_ci_<env> (example: gitops_ci_prod)
- Key Vault = kv-<env>
- Key Vault secret name = SNOWFLAKE_PRIVATE_KEY_BASE64
- You have access to Snowflake admin + Key Vault contributor + Azure app owner for gitops-ci-<env>

High-level safe rotation steps (no downtime preferred)
1) Generate new key pair (admin machine)
   - Generate a new RSA key pair (PKCS#8 PEM for private, public PEM for Snowflake):
     ```bash
     openssl genpkey -algorithm RSA -out rsa_new.pem -pkeyopt rsa_keygen_bits:2048
     openssl rsa -pubout -in rsa_new.pem -out rsa_new.pub
     openssl pkcs8 -topk8 -inform PEM -outform PEM -nocrypt -in rsa_new.pem -out rsa_new_pkcs8.pem
     base64 -w0 rsa_new_pkcs8.pem > rsa_new_pkcs8.pem.base64   # linux
     ```
   - Keep private files offline and secure.

2) Stage public key in Snowflake (test method)
   - If Snowflake supports a secondary key mechanism, add the new public key as a secondary key and test switching. If not, coordinate cutover (see below).
   - Example (if direct replace is required):
     - Notify stakeholders of short maintenance window (if necessary).
     - Run:
       ```sql
       ALTER USER gitops_ci_<env> SET RSA_PUBLIC_KEY = '<contents-of-rsa_new.pub>';
       ```
     - Alternatively, create a second user (gitops_ci_<env>_rot) for testing, set its RSA_PUBLIC_KEY to the new pubkey, grant same role, and test.

3) Update Key Vault secret
   - Update the Key Vault secret value with the new base64 private key:
     ```bash
     az keyvault secret set --vault-name kv-<env> --name SNOWFLAKE_PRIVATE_KEY_BASE64 --value "$(cat rsa_new_pkcs8.pem.base64)"
     ```
   - Key Vault will version the secret; keep the old version for rollback.

4) Test pipeline (dev/qa first)
   - Trigger the pipeline for the environment (or run the workflow manually).
   - Verify the runner obtains the new secret, connects successfully to Snowflake, and migrations (or a simple readonly query) succeed.
   - Inspect Key Vault access logs for the retrieval and Snowflake audit logs for auth events.

5) Cutover (if direct public-key replacement required)
   - If using a single Snowflake user and altering the RSA_PUBLIC_KEY in place:
     - Update Snowflake public key (see step 2).
     - Immediately update Key Vault secret (step 3).
     - Trigger pipeline and confirm connectivity.
     - If failure, roll back by restoring Key Vault secret to previous value (az keyvault secret set with previous base64) or revert Snowflake public key.

6) Rollback plan
   - If the new key fails:
     - Old Key Vault secret version is still available; retrieve old value and set it as the current secret:
       ```bash
       az keyvault secret list-versions --vault-name kv-<env> --name SNOWFLAKE_PRIVATE_KEY_BASE64
       az keyvault secret set --vault-name kv-<env> --name SNOWFLAKE_PRIVATE_KEY_BASE64 --value "<old-base64-value>"
       ```
     - Or restore the previous Snowflake public key from your backup and notify stakeholders.

7) Clean up
   - Securely archive or destroy old private key material (do not leave old private keys on disk).
   - Record rotation event in change log: who rotated, when, secret versions, Snowflake ALTER USER statement used.

Checklist (pre-rotation)
- [ ] Notify stakeholders and schedule maintenance window (if necessary)
- [ ] Ensure you have admin access to Snowflake and Key Vault
- [ ] Backup current Snowflake public key and Key Vault secret version id
- [ ] Generate new key pair and securely store offline
- [ ] Prepare a test plan for pipeline verification

Checklist (post-rotation)
- [ ] Confirm pipeline artifacts run successfully with new key
- [ ] Check Key Vault logs for secret access events
- [ ] Check Snowflake audit logs for auth success on gitops_ci_<env>
- [ ] Document rotation in runbook (include secret version IDs)
- [ ] Destroy old private key file from any temporary machines

Notes and tips
- Prefer to rotate dev/qa first, verify, then rotate production.
- Consider creating a secondary Snowflake CI user for staged cutover to avoid single-user lockstep when Snowflake does not support multiple keys per user.
- Automate rotation verification using a small test job in the pipeline that validates authentication but does not run destructive migrations.

End of runbook.