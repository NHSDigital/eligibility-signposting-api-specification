# GitHub Workflows for eligibility-signposting-api-specification

This directory contains GitHub Actions workflows that automate CI/CD processes for the eligibility-signposting-api-specification project. These workflows manage deployment, tagging, and notifications for different environments (dev, sandbox, preprod, prod) and integrate with external tools like proxygen and Postman.

## Workflows Overview

### 1. dev_sandbox_publish_deploy.yaml

- **Triggers:** On push to `main` branch.
- **Environments:** dev, sandbox.
- **Steps:**
  - Sets a version tag based on the current timestamp.
  - Installs dependencies (Python, Node.js, Poetry, proxygen-cli).
  - Generates and publishes OpenAPI specs to proxygen for dev and sandbox.
  - Publishes the Postman collection to Postman.
  - Tags the deployment in Git (Example tag: spec-20260122155331).
  - Notifies a Slack channel on completion.

### 2. preprod_publish_deploy.yaml

- **Triggers:** Manually via GitHub UI (`workflow_dispatch`).
- **Inputs:** Tag to promote (defaults to latest).
- **Environment:** preprod.
- **Steps:**
  - Checks out the specified tag.
  - Installs dependencies.
  - Generates and publishes the OpenAPI spec to proxygen for preprod.
  - Deploys the spec to the preprod proxygen instance.

### 3. prod_publish_deploy.yaml

- **Triggers:** Manually via GitHub UI (`workflow_dispatch`).
- **Inputs:** Tag to promote (required).
- **Environment:** Prod.
- **Steps:**
  - Checks out the specified tag.
  - Installs dependencies.
  - Generates and publishes the OpenAPI spec to proxygen for Prod.
  - Deploys the spec to the Prod proxygen instance.
  - Creates a GitHub Release for the deployed tag.

## How to Use

### dev & sandbox deployment

- Push changes to the `main` branch.
- The workflow will automatically:
  - Deploy to dev and sandbox.
  - Publish the Postman collection.
  - Tag the deployment.
  - Notify Slack.

### preprod deployment

- Go to the **Actions** tab in GitHub.
- Select **Deploy to preprod** workflow.
- Click **Run workflow**.
- Enter the tag to promote (or use the default `latest`).
- The workflow will deploy the specified tag to preprod.

### prod deployment

- Go to the **Actions** tab in GitHub.
- Select **Deploy to Prod** workflow.
- Click **Run workflow**.
- Enter the tag to promote (must match a tag from previous deployments).
- The workflow will deploy the specified tag to Prod and create a GitHub Release.

## Notes

- All workflows require secrets to be set in the repository (e.g., `PROXYGEN_PRIVATE_KEY`, `POSTMAN_API_KEY`, `SLACK_WORKFLOW_WEBHOOK_URL`, `GITHUB_TOKEN`).
- The tags created follow the format `spec-YYYYMMDDHHMMSS` indicative of the deployment time. This is NOT related to the [specification/eligibility-signposting-api](../specification/eligibility-signposting-api.yaml) version.
- For more details, see the steps in each workflow YAML file.
