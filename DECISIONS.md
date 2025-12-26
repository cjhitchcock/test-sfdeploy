# DECISIONS

This file records key architectural decisions made so far.

- Decision 1: Branch model
  - Use dev / qa / release / main with feature/* branches for development.

- Decision 2: Approvals
  - Require manual PR approvals; Production deployments require GitHub Environment approval.

- Decision 3: Environment configs
  - Non-secret environment-specific values are stored in configs/{dev,qa,prod}.yml in the repo for visibility and review.
  - Secrets (credentials, private keys) are stored in GitHub Environment secrets.

- Decision 4: Migration tool
  - Example uses a custom SQL runner for quick iteration. Plan to adopt Flyway/dbt for production migrations when mature.