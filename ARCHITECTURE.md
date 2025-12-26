## Monitoring and Logging

### Azure Key Vault Logging
To track and audit access to sensitive secrets stored in Azure Key Vault:

1. **Enable Diagnostic Logging**:
    - Navigate to **Azure Portal** → **Key Vault** → **Diagnostic settings** → **Add diagnostic setting**.
    - Configure an audit log destination such as:
        - **Log Analytics Workspace** for querying logs.
        - **Azure Storage** for long-term archival.
        - **Event Hub** for real-time monitoring.
    - Enable the following logging categories:
        - **AuditEvent**: Tracks secret access operations.
        - **AllMetrics**: Tracks overall Key Vault performance.

2. **Set Up Alerts**:
    - Use **Azure Monitor** to create alert rules.
    - Example conditions:
        - Unauthorized access attempts.
        - Suspicious IP addresses accessing Key Vault secrets.

3. **Query Logs**:
    Use Azure Log Analytics to investigate secret access, e.g.:
    ```kql
    AzureDiagnostics
    | where Resource == "kv-dev"
    | where OperationName == "SecretGet"
    | summarize AccessCount=count() by CallerIPAddress, Caller
    | sort by AccessCount desc
    ```

---

### Snowflake Query Logs
1. **Audit Queries**:
    Use the `QUERY_HISTORY` view to analyze executed SQL, e.g.:
    ```sql
    SELECT *
    FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
    WHERE QUERY_TEXT ILIKE '%DROP%';
    ```

2. **Set Up Alerts**:
    Utilize Snowflake Tasks to perform automated query auditing and alerting based on query patterns.