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
  - Improved logging for SQL migrations to include file-specific execution details.
  - Added schema validation stub for pre-migration checks.
  - Implemented retry logic for transient Snowflake errors.
- Updated `.github/workflows/dev-snowflake-migration.yml`:
  - Switched to Managed Identity for Azure.
  - Pinned runner to `ubuntu-22.04`.
  - Added retry logic for migrations.

---

## [1.0.0] - 2025-12-26
### Added
- Initial version of the pipeline.
- GitHub Actions workflow for Snowflake SQL migrations.
- Azure Key Vault integration with GitHub Actions.