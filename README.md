# test-sfdeploy

This repository holds the GitOps CI/CD templates and example scripts for deploying SQL migrations to Snowflake.

What is included in "wip" branch:
- ARCHITECTURE.md - architecture and flow summary
- DECISIONS.md - decision records
- .github/workflows/ - CI/CD workflow templates (dev/qa/release)
- scripts/sql-runner.py - example SQL migration runner using snowflake-connector-python
- scripts/export_config.py - helper to export configs/*.yml values into the Actions environment
- configs/*.yml - environment non-secret configuration (database/schema/warehouse/role)
- sql/migrations/ - example migration

How to get started:
1. Create GitHub Environments: dev, qa, production and add required environment secrets (SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD or SNOWFLAKE_PRIVATE_KEY, SNOWFLAKE_ROLE, SNOWFLAKE_WAREHOUSE, SNOWFLAKE_DATABASE, SNOWFLAKE_SCHEMA).
2. Push feature branches and open PRs to dev to run the dev workflow.
3. Review ARCHITECTURE.md and DECISIONS.md for more details.
