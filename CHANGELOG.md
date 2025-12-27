# Changelog

All notable changes to this project will be documented in this file.  
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]
### Added
- **`ARCHITECTURE.md`** and **`DOCS.md`** files added to document project architecture, usage, and best practices.
- Azure Key Vault logging setup instructions added for secret access auditing.
- Snowflake SQL query monitoring examples added.

### Changed
- Updated `sql-runner.py`:
  - Added command-line argument support for specifying migrations directory.
  - Added sorting of SQL files to ensure consistent execution order.
  - Added file type checking to only process .sql files.
  - Improved logging to record the path of each executed SQL file.
  - Added schema validation stub for pre-migration checks.
- Updated `.github/workflows/dev-snowflake-migration.yml`:
  - Switched to OIDC authentication with Azure (client-id, tenant-id, subscription-id).
  - Changed branch trigger from `cjh-research` to `dev`.
  - Pinned runner to `ubuntu-22.04`.
  - Added retry logic in the workflow bash script for transient errors during migrations.
  - Made requirements.txt installation conditional.
- Updated `scripts/create-azure-env.sh`:
  - Fixed secret name from `SNOWFLAKE_PRIVATE_KEY` to `SNOWFLAKE_PRIVATE_KEY_BASE64`.
  - Added output suppression to prevent secret values from appearing in logs.
  - Added documentation for required environment variables.

---

## [1.0.0] - 2025-12-26
### Added
- Initial version of the pipeline.
- GitHub Actions workflow for Snowflake SQL migrations.
- Azure Key Vault integration with GitHub Actions.