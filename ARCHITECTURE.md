# ARCHITECTURE

This repository implements a GitOps CI/CD pipeline for Snowflake with the following branch model and promotion flow:

- Branches:
  - feature/* : Developer feature branches (short lived)
  - dev       : Integration branch; auto-deploys to Dev environment
  - qa        : Promotion from dev; deploys to QA environment
  - release   : Branch used to deploy to Production; after successful deploy it is promoted/merged into main
  - main      : Canonical production history; protected

- Promotion flow summary:
  1. Developer creates feature/* branch and opens PR into dev.
  2. After review & CI, feature is merged into dev and deployments to Dev run automatically.
  3. Create PR dev -> qa, run integration tests and reviews; merge triggers QA deployments.
  4. Create or update release branch from qa; pushes to release trigger Production workflow which is gated with manual environment approval.
  5. After successful production deploy, create/automate PR release -> main and merge with tags.

- Environments and secrets:
  - Use GitHub Environments: dev, qa, production. Store credentials as environment secrets.
  - Non-sensitive environment-specific values (database names, schemas, warehouse sizes) live in configs/*.yml in the repo.

- Migration tooling:
  - A simple SQL runner is included as an example. For production, consider migrating to Flyway, Liquibase or dbt.
