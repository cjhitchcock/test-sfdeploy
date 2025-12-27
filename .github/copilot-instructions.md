# GitHub Copilot Instructions

## Repository Overview

This repository implements a GitOps CI/CD pipeline for deploying SQL migrations to Snowflake. It provides workflow templates and example scripts for automated database deployment across multiple environments.

## Branch Model and Workflow

Follow this strict branch hierarchy and promotion flow:

- **feature/\*** - Developer feature branches (short-lived)
- **dev** - Integration branch; auto-deploys to Dev environment
- **qa** - Promotion from dev; deploys to QA environment
- **release** - Deploys to Production (requires manual approval); merged into main after success
- **main** - Canonical production history (protected)

**Promotion Flow:**
1. Create feature branch → open PR to `dev`
2. After review and CI, merge to `dev` → auto-deploy to Dev
3. Create PR `dev` → `qa` → merge triggers QA deployment
4. Update `release` branch from `qa` → triggers Production workflow (manual approval required)
5. After successful production deploy, create PR `release` → `main` and merge

## Project Structure

```
.
├── configs/          # Environment-specific configuration (non-secrets)
│   ├── base.yml      # Default values
│   ├── dev.yml       # Dev environment config
│   ├── qa.yml        # QA environment config
│   └── prod.yml      # Production environment config
├── scripts/          # Deployment and utility scripts
│   ├── sql-runner.py       # Snowflake SQL migration runner
│   ├── export_config.py    # Export YAML configs to GitHub Actions environment
│   └── create-azure-env.sh # Azure environment setup helper
├── sql/              # SQL migrations
│   └── migrations/   # Migration files (run in alphabetical order)
├── ARCHITECTURE.md   # Architecture and flow documentation
├── DECISIONS.md      # Architecture decision records
└── README.md         # Getting started guide
```

## Python Coding Standards

### Style and Conventions
- Use Python 3 with type hints where appropriate
- Follow PEP 8 style guidelines
- Use descriptive variable names
- Include docstrings for modules and functions
- Prefer explicit error handling with try/except blocks
- Use logging instead of print statements (except for CLI output)

### Example Patterns
```python
# Logging setup
import logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Environment variable handling
env = os.environ
value = env.get("VARIABLE_NAME")
if not value:
    logger.error("Missing required environment variable: VARIABLE_NAME")
    raise SystemExit(1)
```

## SQL Migration Standards

### File Naming
- Use sequential numbering: `001__description.sql`, `002__another_change.sql`
- Use double underscores to separate number from description
- Use lowercase and underscores for descriptions
- Migrations run in alphabetical order

### SQL Style
- Use uppercase for SQL keywords (CREATE, TABLE, IF NOT EXISTS, etc.)
- Include `IF NOT EXISTS` or `IF EXISTS` for idempotent migrations
- Use semicolons to separate statements
- Include comments explaining complex migrations

### Example
```sql
-- Example migration: create a sample table if not exists
CREATE TABLE IF NOT EXISTS sample_table (
  id NUMBER PRIMARY KEY,
  created_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP
);
```

## Configuration Management

### Non-Secret Configuration
- Store environment-specific non-secret values in `configs/{env}.yml`
- These files are committed to the repository for visibility
- Use `export_config.py` to load values into GitHub Actions environment
- Configuration keys are converted to UPPERCASE with underscores

### Secret Management
- **NEVER** commit secrets, credentials, or private keys to the repository
- Store secrets in GitHub Environment Secrets:
  - `SNOWFLAKE_ACCOUNT`
  - `SNOWFLAKE_USER`
  - `SNOWFLAKE_PASSWORD` (or `SNOWFLAKE_PRIVATE_KEY_BASE64`)
  - `SNOWFLAKE_ROLE`
  - `SNOWFLAKE_WAREHOUSE`
  - `SNOWFLAKE_DATABASE`
  - `SNOWFLAKE_SCHEMA`

### Security Best Practices
- Prefer private key authentication over password authentication
- Use base64-encoded PKCS#8 PEM format for private keys
- Store private keys in `SNOWFLAKE_PRIVATE_KEY_BASE64` environment variable
- Support optional `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` for encrypted keys
- Never log sensitive values (credentials, keys, passwords)

## Snowflake Authentication

The `sql-runner.py` script supports two authentication methods:

1. **Private Key Authentication (Preferred)**
   - Set `SNOWFLAKE_PRIVATE_KEY_BASE64` with base64-encoded PKCS#8 PEM key
   - Optionally set `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` if key is encrypted

2. **Password Authentication (Fallback)**
   - Set `SNOWFLAKE_PASSWORD` environment variable

## Development Workflow

1. **Before Making Changes:**
   - Review `ARCHITECTURE.md` for system design
   - Review `DECISIONS.md` for architectural decisions
   - Understand the branch model before creating PRs

2. **When Adding Features:**
   - Create feature branch from `dev`
   - Update relevant documentation if architecture changes
   - Test locally with appropriate Snowflake credentials
   - Open PR to `dev` branch (never directly to main)

3. **When Modifying SQL Runner:**
   - Maintain backward compatibility with existing migrations
   - Preserve error handling and logging patterns
   - Do not log sensitive information
   - Update docstrings if function signatures change

4. **When Adding Migrations:**
   - Follow sequential numbering convention
   - Make migrations idempotent (use IF EXISTS/IF NOT EXISTS)
   - Test migrations in dev environment first
   - Document complex migrations with comments

## GitHub Actions Integration

- Use `export_config.py` to load environment configs into workflows
- Expect environment variables to be set from GitHub Secrets
- Workflows should be environment-specific (dev/qa/production)
- Production deployments require manual approval via GitHub Environments

## Future Considerations

- Migration tool may migrate from custom SQL runner to Flyway, Liquibase, or dbt
- When suggesting improvements, maintain compatibility with existing patterns
- Consider the GitOps workflow when proposing CI/CD changes
