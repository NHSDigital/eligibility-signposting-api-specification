# GitHub Workflows for eligibility-signposting-api-specification

This directory contains GitHub Actions workflows that automate CI/CD processes for the eligibility-signposting-api-specification project. These workflows manage deployment, tagging, and notifications for different environments (Dev, Sandbox, Preprod, Prod) and integrate with external tools like Proxygen and Postman.

## Workflows Overview

### 1. dev_sandbox_publish_deploy.yaml

- **Triggers:** On push to `main` branch.
- **Environments:** Dev (internal-dev), Sandbox.
- **Steps:**
  - Sets a version tag based on the current timestamp.
  - Installs dependencies (Python, Node.js, Poetry, proxygen-cli).
  - Generates and publishes OpenAPI specs to Proxygen for Dev and Sandbox.
  - Publishes the Postman collection to Postman.
  - Tags the deployment in Git (Example tag: spec-20260122155331).
  - Notifies a Slack channel on completion.

### 2. preprod_publish_deploy.yaml

- **Triggers:** Manually via GitHub UI (`workflow_dispatch`).
- **Inputs:** Tag to promote (defaults to latest).
- **Environment:** Preprod.
- **Steps:**
  - Checks out the specified tag.
  - Installs dependencies.
  - Generates and publishes the OpenAPI spec to Proxygen for Preprod.
  - Deploys the spec to the Preprod Proxygen instance.

### 3. prod_publish_deploy.yaml

- **Triggers:** Manually via GitHub UI (`workflow_dispatch`).
- **Inputs:** Tag to promote (required).
- **Environment:** Prod.
- **Steps:**
  - Checks out the specified tag.
  - Installs dependencies.
  - Generates and publishes the OpenAPI spec to Proxygen for Prod.
  - Deploys the spec to the Prod Proxygen instance.
  - Creates a GitHub Release for the deployed tag.

## How to Use

### Dev & Sandbox Deployment

- Push changes to the `main` branch.
- The workflow will automatically:
  - Deploy to Dev and Sandbox.
  - Publish the Postman collection.
  - Tag the deployment.
  - Notify Slack.

### Preprod Deployment

- Go to the **Actions** tab in GitHub.
- Select **Deploy to Preprod** workflow.
- Click **Run workflow**.
- Enter the tag to promote (or use the default `latest`).
- The workflow will deploy the specified tag to Preprod.

### Prod Deployment

- Go to the **Actions** tab in GitHub.
- Select **Deploy to Prod** workflow.
- Click **Run workflow**.
- Enter the tag to promote (must match a tag from previous deployments).
- The workflow will deploy the specified tag to Prod and create a GitHub Release.

## Notes

- All workflows require secrets to be set in the repository (e.g., `PROXYGEN_PRIVATE_KEY`, `POSTMAN_API_KEY`, `SLACK_WORKFLOW_WEBHOOK_URL`, `GITHUB_TOKEN`).
- The tags created follow the format `spec-YYYYMMDDHHMMSS` indicative of the deployment time. This is NOT related to the [specification/eligibility-signposting-api](../specification/eligibility-signposting-api.yaml) version.
- For more details, see the steps in each workflow YAML file.
