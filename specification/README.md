# Vaccination Eligibility Data Product - Specification

## Overview

The `eligibility-signposting-api` is based on an OpenAPI specification maintained at `/specification/eligibility-signposting-api.yaml`. We use [Redocly CLI](https://redocly.com/docs/cli) to inject environment-specific elements into the base specification, allowing us to publish to different environments without manual editing or maintaining duplicate specifications.

## Directory Structure

Each directory contains environment specific configuration for the specification. If the configuration doesn't exist for your chosen environment, then add it.

### `components/security/`

Contains environment-specific security configurations for each endpoint.

### `x-nhsd-apim/`

Contains APIM extensions to the OpenAPI specification with deployment requirements:

- **access**: Environment-specific access patterns
- **rate-limit**: API rate limiting configurations
- **target**: API backend details for proxy configuration

## Generating Environment-Specific Specifications

To build a specification for a specific environment:

1. Make sure you've run the initial setup command `make install-node`.
2. Set the target environment using the `APIM_ENV` parameter (dev, test, preprod, prod, sandbox)
3. Run `make construct-spec` from the repository root, which:
   - Updates templates with environment-specific values
   - Uses Redocly to compile the complete specification to `build/specification/$(APIM_ENV)/`
4. For the `sandbox` environment, run `make generate-sandbox-spec` to convert the specification to JSON and save it to `sandbox/specification/` for immediate use.

### Deploying of Environment-Specific Specifications to Apigee

See the [Proxygen CLI user guide](https://nhsd-confluence.digital.nhs.uk/spaces/APM/pages/804495095/Proxygen+CLI+user+guide#ProxygenCLIuserguide-Settingupsettingsandcredentials)

We deploy our specifications using the Proxygen CLI. In order to do this, the following steps need to be performed:

1. Construct the specification for the environment of your choice, following the instructions above.
2. Activate a poetry environment `poetry env activate` - you may need to run `make install-python` to install poetry etc. first.
3. Run `make retrieve-proxygen-key` from the root directory to retrieve the private key needed to authenticate with Proxygen.
4. Run `make setup-proxygen-credentials` from the root directory to set up credentials needed to interact with our API proxy.
5. Run `proxygen instance deploy <environment> eligibility-signposting-api ./build/specification/<env>/eligibility-signposting-api.yaml` to deploy the specification to
   a chosen environment.

### Publishing specifications

1. To get the currently published specification run `make get-spec` for production or `make get-spec-uat` for non-production. This will return an error if a specification is not deployed.
2. To publish a specification, generate an appropriate specification (prod for production, preprod for uat) above then run `make publish-spec` for production or `make publish-spec-uat` for non-production.
3. To delete a specification, run `make delete-spec` for production or `make delete-spec-uat` for non-production
