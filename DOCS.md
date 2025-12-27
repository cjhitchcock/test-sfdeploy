---

## Azure Key Vault Logging

### Enable Audit Logs
To monitor sensitive secret usage:
1. Open your Azure Key Vault in the Azure Portal.
2. Navigate to **Diagnostic settings**.
    - Select "Add diagnostic setting."
    - Choose a log destination (e.g., Log Analytics, Storage Account, Event Hub).
    - Enable the following log categories:
        - **AuditEvent**: Tracks all secret access (e.g., `SecretGet`).
        - **AllMetrics**: Tracks operational data and performance.

### Query Logs via Azure Log Analytics
You can run KQL queries to investigate access to sensitive secrets. For example:
```kql
AzureDiagnostics
| where Resource == "kv-dev"
| where OperationName == "SecretGet"
| summarize AccessCount=count() by CallerIPAddress, Caller
```

### Set Alerts for Suspicious Behavior
- Use **Azure Monitor** to create real-time alerts.
- Examples:
  - **Condition**: Any unusual secret access outside business hours.
  - **Action**: Notifies a security admin via email, SMS, or webhook.

---

## Snowflake Query Audit

To monitor executed SQL queries:
1. Leverage the `ACCOUNT_USAGE.QUERY_HISTORY` table:
    ```sql
    SELECT *
    FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
    WHERE QUERY_TEXT ILIKE '%DROP%' OR QUERY_TEXT ILIKE '%DELETE%';
    ```

2. Set up a Snowflake Task to run these queries periodically and trigger alerts.