# Review Checklist

This checklist provides a structured order of operations to review work to date in the cjh-research branch without testing.

---

## 1. Git Repository State

### Check Commit History
- Use `git log` or GitHub’s **Commits tab**.
- Verify:
  - Commit messages are clear and reflect purpose.
  - Recent commits match planned updates (e.g., workflow improvements, script documentation).
  - No unnecessary commits.

#### Git Commands:
```bash
git log --oneline
```

### Check for Divergence
- Ensure local branch matches remote branch:
```bash
git fetch origin
git log origin/cjh-research..cjh-research --oneline
```

---

## 2. Workflow Files Review

### Inspect `.github/workflows/dev-snowflake-migration.yml`
Focus areas:
- **Trigger Setup**:
  - Appropriate `on:` events (e.g., `push` to `cjh-research`, `workflow_dispatch`).
- **Secrets Security**:
  - Ensure no secrets are hardcoded.
  - Secrets handled securely (Azure Key Vault or GitHub Secrets).
- **Error Handling**:
  - Check retry logic for transient failures.

#### Things to Look For:
- Correct Managed Identity setup:
```yaml
uses: azure/login@v1
with:
  managed-identity: true
```
- Pinned runner version:
```yaml
runs-on: ubuntu-22.04
```

### Job Steps Order
- Logical step flow:
  1. Fetch code via `actions/checkout`.
  2. Authenticate to Azure.
  3. Fetch secrets securely.
  4. Set up environment (e.g., Python, pip packages).
  5. Execute tasks (Snowflake SQL migrations).

---

## 3. Code Review

### Inspect the Python Code
1. **Functionality**:
   - Ensure script runs SQL sequentially and logs progress.
   - Confirm retry logic for transient failures.

2. **Error Handling**:
   - Look for robust exception handling:
     ```python
     try:
         # critical block
     except Exception as e:
         logger.error("Error occurred: %s", e)
     ```

3. **Logging**:
   - Confirm logs provide details for each SQL file.

4. **Security**:
   - Sensitive secrets fetched from `os.environ` (not hardcoded).

### Dependencies
- Confirm pinned versions in `requirements.txt`:
```plaintext
snowflake-connector-python==3.1.0
```

---

## 4. Documentation

### High-Level Docs
1. **`ARCHITECTURE.md`**:
   - Explains the overall pipeline design.
   - Includes:
     - Workflow structure.
     - Secret management.
     - Key design decisions.

2. **`DOCS.md`**:
   - Covers setup and usage instructions.
   - Includes:
     - Azure Key Vault managed identity.
     - SQL migration management.

3. **`CHANGELOG.md`**:
   - Lists all notable changes clearly.

---

## 5. Repository Configuration

### Branch Protection Rules
- Ensure `main` is restricted from direct pushes.
- Unprotected `cjh-research` branch acceptable for development/testing.

### Secrets Management
1. Confirm Key Vault diagnostics:
   - Logging enabled for AuditEvents and AllMetrics.
2. Check GitHub secrets:
   - Environment-sensitive variables stored securely.

---

## 6. Recommendations for Final Steps

### Workflow Run
- Trigger workflow manually to validate steps.
- Review GitHub Actions logs for success/errors.

### Snowflake Query Audit
- Use `QUERY_HISTORY` view for manual checks:
```sql
SELECT *
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE QUERY_TEXT ILIKE '%DROP%';
```

---

This checklist ensures all aspects of the branch are reviewed in a structured order, covering code validity, security, and documentation alignment.