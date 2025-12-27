# SNOWFLAKE_PIPELINE_AUTH

## Overview
This document provides guidelines for authenticating Snowflake pipelines securely.

## Handling SNOWFLAKE_PRIVATE_KEY_PASSPHRASE
When working with a passphrase-protected private key, follow the steps below to ensure secure usage and handling:

1. **Secure Storage**: Store the private key passphrase securely in an environment variable called `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE`.
2. **Access Control**: Limit access to the environment variable to only those scripts or applications that require it.
3. **Environment Configuration**: Set the environment variable in the deployment configuration to avoid hardcoding sensitive details directly in the codebase.
4. **Usage in the Pipeline**: Modify the Snowflake authentication setup in your pipeline to retrieve the passphrase from the `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` environment variable.
5. **Testing**: Verify that pipelines using passphrase-protected keys can authenticate successfully during testing and production runs.

By following these steps, you ensure that the `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` is managed securely within your pipeline workflows.
