# GitHub Actions -> Snowflake Authentication (Option 3: per‑environment Azure AD app + Key Vault + per‑env Snowflake key pairs)

Status: draft — commit to wip branch (snowflake-ExcellentData)

Purpose
- Document the recommended authentication & secret management architecture for CI/CD pipelines that deploy SQL changes to Snowflake.
- Pattern: per‑environment isolation using a separate Azure AD application (federated identity), a dedicated Key Vault, and a unique RSA key pair + Snowflake CI user per environment.
- Audience: Snowflake DBAs and engineers with Azure experience and coding knowledge.
- Scope: authentication and security for the pipelines only (not the full pipeline logic).

Repository / environment example used throughout
- GitHub repo: `cjhitchcock/snowflake-ExcellentData`
- Snowflake databases:
  - dev: `dev_ExcellentData`
  - qa: `qa_ExcellentData`
  - prod: `ExcellentData`

Why Option 3 (per‑environment app + vault + key pair)?
- Strong isolation: compromising dev credentials does not affect qa/prod.
- Least privilege & independent lifecycle: keys and CI users can be rotated or revoked individually.
- Granular auditing: Key Vault and AAD logs map to environment-specific app principals.
- Safe production posture: allow different operational policies for production (conditional access, monitoring, stricter rotation).

High-level architecture (per environment)
- Azure AD App Registration: `gitops-ci-<env>` (has a federated identity credential trusting GitHub Actions OIDC for this repo+environment).
- Azure Key Vault: `kv-<env>` holding `SNOWFLAKE_PRIVATE_KEY_BASE64` (base64 of PKCS#8 PEM), plus other environment-specific secrets (account, role, warehouse, database, schema).
- GitHub Actions:
  - Workflow targets `environment: <env>` in its job.
  - `azure/login` (OIDC) uses the app `client-id` and tenant id (no client secret).
  - Action fetches secret from the environment's Key Vault and sets it as runtime environment variable for the migration runner step.
- Snowflake:
  - One CI user per environment: `gitops_ci_dev`, `gitops_ci_qa`, `gitops_ci_prod`
  - Each user has an RSA public key set (RSA_PUBLIC_KEY) that matches the corresponding Key Vault private key.

Pros / Cons (concise)

Pros
- Strongest isolation and security boundary per environment.
- No long‑lived secrets stored in GitHub (OIDC + Key Vault).
- Centralized rotation and better auditability (Key Vault logs).
- Ability to apply stricter Azure controls to production app (conditional access, MFA on management plane).

Cons
- Operational complexity: more Azure objects to manage (3 apps, 3 vaults).
- Slightly more setup time and procedural overhead for CI onboarding.
- More objects to monitor and rotate; requires good documentation and runbooks.

Step-by-step Setup (per environment). Use these steps for dev, qa, prod. Replace `<env>` with `dev`, `qa`, or `prod`. Example for production uses names `gitops-ci-prod` and `kv-prod`.

A. Prepare RSA key pair (on a secure admin machine)
- Create a PKCS#8 private key and public key in PEM:

  ```bash
  # Generate RSA key (2048 or 4096 bits)
  openssl genpkey -algorithm RSA -out rsa_key.pem -pkeyopt rsa_keygen_bits:2048

  # Extract public key PEM (for Snowflake)
  openssl rsa -pubout -in rsa_key.pem -out rsa_key.pub

  # Convert private key to unencrypted PKCS#8 PEM for Snowflake connector
  openssl pkcs8 -topk8 -inform PEM -outform PEM -nocrypt -in rsa_key.pem -out rsa_key_pkcs8.pem
  ```

- Base64‑encode private PKCS#8 PEM (single-line, no wrapping):

  Linux:
  ```bash
  base64 -w0 rsa_key_pkcs8.pem > rsa_key_pkcs8.pem.base64
  ```

  macOS:
  ```bash
  base64 rsa_key_pkcs8.pem | tr -d '\n' > rsa_key_pkcs8.pem.base64
  ```

- Keep `rsa_key.pem` and `rsa_key_pkcs8.pem` securely offline; you will copy the base64 file contents into Key Vault.

B. Create the Snowflake CI user and role (one per env)
- Connect to Snowflake as an admin and run (replace placeholders and paste your public key content where shown):

  ```sql
  -- Example for production (adjust names for dev/qa)
  CREATE ROLE IF NOT EXISTS ci_deployer_prod;

  -- Grant minimal privileges required for migrations (adjust to your needs)
  GRANT USAGE ON WAREHOUSE my_warehouse TO ROLE ci_deployer_prod;
  GRANT USAGE ON DATABASE ExcellentData TO ROLE ci_deployer_prod;
  GRANT USAGE ON SCHEMA ExcellentData.public TO ROLE ci_deployer_prod;
  -- Grant DDL as required:
  GRANT CREATE TABLE ON SCHEMA ExcellentData.public TO ROLE ci_deployer_prod;

  -- Create CI user and set the RSA public key (paste full rsa_key.pub content here)
  CREATE USER IF NOT EXISTS gitops_ci_prod
    DEFAULT_ROLE = ci_deployer_prod
    MUST_CHANGE_PASSWORD = FALSE
    COMMENT = 'GitHub Actions CI user for production'
    RSA_PUBLIC_KEY = '-----BEGIN PUBLIC KEY-----
  MIIBIjANBgkq...   -- paste rsa_key.pub contents including BEGIN/END
  -----END PUBLIC KEY-----';

  GRANT ROLE ci_deployer_prod TO USER gitops_ci_prod;
  ```

- Repeat for dev/qa with appropriately named roles/users and database/schema names:
  - dev: `ci_deployer_dev`, `gitops_ci_dev`, database `dev_ExcellentData`
  - qa:  `ci_deployer_qa`,  `gitops_ci_qa`,  database `qa_ExcellentData`

C. Create Azure resources per environment (recommended using az CLI + Azure Portal)
- Overview (per env):
  - App Registration: `gitops-ci-<env>` (note the `appId` and `objectId`)
  - Federated Identity Credential: subject restricted to the repo + environment
  - Key Vault: `kv-<env>` with secret `SNOWFLAKE_PRIVATE_KEY_BASE64`
  - Grant the app `get` + `list` secret permissions on the vault

1) Create App Registration (CLI)

```bash
# create the AAD app
az ad app create --display-name "gitops-ci-<env>" \
  --available-to-other-tenants false \
  --identifier-uris "api://gitops-ci-<env>" \
  --query "{appId:appId,id:id}" -o json
```

- Save `appId` (client id) and `id` (object id) from the command output.

2) Create a Service Principal (so you can set Key Vault RBAC / policies)

```bash
az ad sp create --id <appId>
```

3) Add a federated identity credential (so GitHub Actions OIDC can exchange tokens)
- You can create the federated credential in the Azure Portal (App Registration → Certificates & secrets → Federated credentials → Add), OR use Graph REST:

Example using az rest (replace `{appObjectId}` with the `id` value from step 1):

```bash
az rest --method POST \
  --uri "https://graph.microsoft.com/v1.0/applications/{appObjectId}/federatedIdentityCredentials" \
  --headers "Content-Type=application/json" \
  --body '{
    "name": "github-actions-<env>",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:cjhitchcock/snowflake-ExcellentData:environment:<env>",
    "description": "Federated credential for GitHub Actions (repo:cjhitchcock/snowflake-ExcellentData, environment:<env>)",
    "audiences": ["api://AzureADTokenExchange"]
  }'
```

Notes:
- The `subject` is critical. Use:
  - `repo:<owner>/<repo>:environment:<env>` to limit tokens to runs that target the GitHub environment `<env>`.
  - Alternatively, you may use `repo:<owner>/<repo>:ref:refs/heads/<branch>` if you prefer branch-based restriction.
- The `audiences` value `api://AzureADTokenExchange` is standard for Actions → Azure OIDC flows.

4) Create Key Vault and add the private key secret

```bash
# create key vault
az keyvault create --name "kv-<env>" --resource-group "<your-rg>" --location "<your-location>"

# set policy to allow the app principal to get/list secrets (using appId or sp object id)
# Using the service principal's appId (client id):
az keyvault set-policy --name "kv-<env>" --spn "<appId>" --secret-permissions get list

# add the private key secret (base64 content)
az keyvault secret set --vault-name "kv-<env>" --name "SNOWFLAKE_PRIVATE_KEY_BASE64" \
  --value "$(cat rsa_key_pkcs8.pem.base64)"
```

Notes:
- You may choose Key Vault access policies (set-policy) or Azure RBAC (role assignment) depending on your org preference. `az keyvault set-policy` is straightforward: it supports `--spn` for a client id.

5) Repeat for dev, qa, prod — use separate app registrations and separate key vaults.
- When creating federated credentials, ensure `subject` is environment-specific:
  - `repo:cjhitchcock/snowflake-ExcellentData:environment:dev`
  - `repo:cjhitchcock/snowflake-ExcellentData:environment:qa`
  - `repo:cjhitchcock/snowflake-ExcellentData:environment:production`

D. GitHub repository setup
1) Create GitHub Environments
- In the repository settings create environments: `dev`, `qa`, `production`.
- For `production`, configure required reviewers (one or more approvers) to gate deployments.

2) Store non-secret app identifiers in the repo (or secrets)
- The Azure App `client-id` (appId) and `tenant-id` are needed by `azure/login`. The client-id is not a secret, but you can store it as an org/repo secret to avoid editing workflows.
- Recommended secrets to store (repo secrets or environment secrets as appropriate):
  - For each environment store:
    - `AZURE_CLIENT_ID_<ENV>` (client id of the env app)
    - `AZURE_TENANT_ID` (tenant id — same across envs)
  - No client secret is required because we use OIDC federated credentials.

E. GitHub Actions workflow example (per environment)
- Job must declare `environment: <env>` (this ties to the GitHub Environment UI and approval gating).
- The workflow logs into Azure with OIDC (no secret), fetches the secret from Key Vault, decodes if necessary, and runs the migration.

Example job snippet (production):

```yaml
jobs:
  deploy-prod:
    runs-on: ubuntu-latest
    environment: production

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Azure login (OIDC)
        uses: azure/login@v1
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID_PROD }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          enable-oidc: true

      - name: Get private key from Key Vault
        id: kv
        uses: azure/get-keyvault-secrets@v1
        with:
          keyvault: 'kv-prod'
          secrets: 'SNOWFLAKE_PRIVATE_KEY_BASE64'
      # Do not print secret – export to runner env instead
      - name: Export SNOWFLAKE_PRIVATE_KEY_BASE64 to GITHUB_ENV
        run: echo "SNOWFLAKE_PRIVATE_KEY_BASE64=${{ steps.kv.outputs.SNOWFLAKE_PRIVATE_KEY_BASE64 }}" >> $GITHUB_ENV

      - name: Install deps
        run: |
          python -m pip install --upgrade pip
          pip install pyyaml snowflake-connector-python cryptography

      - name: Export other non-secret config from repo to env (example)
        run: |
          echo "SNOWFLAKE_ACCOUNT=${{ secrets.SNOWFLAKE_ACCOUNT_PROD }}" >> $GITHUB_ENV
          echo "SNOWFLAKE_USER=gitops_ci_prod" >> $GITHUB_ENV
          echo "SNOWFLAKE_ROLE=ci_deployer_prod" >> $GITHUB_ENV
          echo "SNOWFLAKE_WAREHOUSE=my_warehouse" >> $GITHUB_ENV
          echo "SNOWFLAKE_DATABASE=ExcellentData" >> $GITHUB_ENV
          echo "SNOWFLAKE_SCHEMA=public" >> $GITHUB_ENV

      - name: Run migrations
        run: |
          python scripts/sql-runner.py sql/migrations
```

Notes:
- `azure/get-keyvault-secrets` requires the action to be able to acquire an Azure token via `azure/login`. This works because the federated credential allows the Action's OIDC token to be exchanged for an Azure AD token for the app.
- Set the other environment-specific secrets (SNOWFLAKE_ACCOUNT_PROD) in repo secrets or, better, store them as Key Vault secrets and fetch them similarly.
- Ensure the job executes only after any required approval (production environment will block until approved if configured).

F. sql-runner.py adjustments (summary)
- Make the runner support loading `SNOWFLAKE_PRIVATE_KEY_BASE64` (base64 PKCS#8 PEM) and optional `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE`.
- Use the cryptography library to load PEM into bytes acceptable to `snowflake.connector.connect(private_key=...)`.
- The runner should never log secret contents; wipe temporary files if used.

G. Testing & verification
- Test in `dev` first: commit changes to a branch that triggers the dev workflow (job environment: dev). Confirm `azure/login` + `get-keyvault-secrets` can retrieve the private key and the runner connects to `dev_ExcellentData`.
- Promote to `qa` and test similarly.
- For `production`, ensure environment approvers are configured before running.

H. Operational & security best practices
- Limit federated credential `subject` as narrowly as possible (repo + environment or repo + branch).
- Enable Key Vault logging and ship logs to a Log Analytics workspace or SIEM.
- Protect Key Vault (soft delete & purge protection) and enforce RBAC least privilege.
- Use conditional access (Azure AD) for production app management operations.
- Rotate RSA keys on a schedule and document the rotation process (generate new key pair, update Snowflake user RSA_PUBLIC_KEY, update Key Vault secret).
- Avoid ever printing secrets in workflow logs. Use `$GITHUB_ENV` or in‑memory variables.
- Consider self‑hosted runners in an Azure VNet if Snowflake account requires IP allowlisting.
- Harden the Snowflake CI user with the minimal set of privileges needed to run migrations; do not grant broader roles than necessary.

I. Example: key rotation process (high level)
1. Generate new RSA key pair for `<env>`.
2. Add new public key value as a second field or run `ALTER USER gitops_ci_<env> SET RSA_PUBLIC_KEY = '<new public key>';`
   - Optionally: Snowflake supports adding a secondary public key? (If not, coordinate cutover).
3. Update Key Vault secret `SNOWFLAKE_PRIVATE_KEY_BASE64` (replace value).
4. Deploy pipeline test (dev/qa) to validate new key.
5. Confirm logs and connectivity, then schedule removal of old key if used.

J. Useful CLI snippets (summary)

- Create Key Vault and set policy:
  ```bash
  az keyvault create --name kv-prod --resource-group rg-xxx --location eastus
  az keyvault set-policy --name kv-prod --spn <appId> --secret-permissions get list
  az keyvault secret set --vault-name kv-prod --name SNOWFLAKE_PRIVATE_KEY_BASE64 --value "$(cat rsa_key_pkcs8.pem.base64)"
  ```

- Create federated credential (az rest example):
  ```bash
  az rest --method POST \
    --uri "https://graph.microsoft.com/v1.0/applications/{appObjectId}/federatedIdentityCredentials" \
    --headers "Content-Type=application/json" \
    --body '{
      "name": "github-actions-prod",
      "issuer": "https://token.actions.githubusercontent.com",
      "subject": "repo:cjhitchcock/snowflake-ExcellentData:environment:production",
      "description": "GitHub Actions OIDC for production",
      "audiences": ["api://AzureADTokenExchange"]
    }'
  ```

K. Appendix: Checklist to finish setup
- [ ] Create per‑env RSA key pairs (dev, qa, prod).
- [ ] Create per‑env Snowflake CI users and set RSA public keys.
- [ ] Create per‑env Azure AD apps and federated credentials scoped to repo + environment.
- [ ] Create per‑env Key Vaults and store SNOWFLAKE_PRIVATE_KEY_BASE64.
- [ ] Grant each app access to only its Key Vault via `az keyvault set-policy`.
- [ ] Configure GitHub Environments (dev/qa/production) and required approvers for production.
- [ ] Update workflows to `azure/login` (OIDC) and fetch secrets from the appropriate Key Vault.
- [ ] Update `scripts/sql-runner.py` to support private key auth via `cryptography`.
- [ ] Test end‑to‑end in dev → qa → production with approvals.

If you want, next steps I can take for you (pick one)
- Produce the ready-to-commit Markdown file (this file) on the wip branch (I can provide the file contents for you to commit).
- Generate a ready-to-apply shell script and az CLI commands for creating one environment (dev) so you can repeat for qa/prod.
- Produce the exact `sql-runner.py` patch and the updated workflow snippets for the three workflows (deploy-dev, deploy-qa, deploy-release) to install cryptography and fetch Key Vault secrets.
- Provide a short runbook for key rotation with exact Snowflake ALTER USER statements and Key Vault secret update steps.

End of document.