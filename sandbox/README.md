# Sandbox environment

The sandbox environment uses:

* [OpenAPI Generator CLI](https://github.com/OpenAPITools/openapi-generator-cli) to validate the specification and convert it from .yaml to .json for use in the sandbox.
* [Prism](https://stoplight.io/open-source/prism) as a mock server.
* A flask proxy to allow us to inject specific examples based on request attributes.

## Developer instructions

Run the following command to start the sandbox environment:

```bash
make spec
make up
```

This will start the sandbox environment on localhost port 9000.

```bash
make down
```

This will stop the sandbox environment.

### Example curl calls

There are a number of examples of responses which can be returned by passing specific NHS Numbers in the patient query parameter:

```bash
 curl -X GET "http://0.0.0.0:9000/patient-check/<NHS_NUMBER>
```

or for sandbox:
```bash
  curl -X GET "https://sandbox.api.service.nhs.uk/eligibility-signposting-api/patient-check/1"  -H "accept: application/json" -H "apikey: g1112R_ccQ1Ebbb4gtHBP1aaaNM"
```

#### Example scenarios

| Patient ID   | Response                                                                                                                              |
|--------------|---------------------------------------------------------------------------------------------------------------------------------------|
| 50000000001  | RSV - Actionable due to membership of an Age Cohort including suggested actions (with booking)                                        |
| 50000000002  | RSV - Actionable due to membership of an Age Cohort including suggested action (not booking)                                          |
| 50000000003  | RSV - Actionable due to membership of an alternative Age Cohort including suggested action (not booking)                              |
| 50000000004  | RSV - Actionable due to membership of an Age Cohort including suggested action (existing national booking)                            |
| 50000000005  | RSV - Actionable due to membership of an Age Cohort including suggested actions (not booking)                                         |
| 50000000006  | RSV - Not Actionable despite to membership of an Age Cohort with reasoning of already vaccinated                                      |
| 50000000007  | RSV - Not Actionable despite to membership of an Age Cohort with reasoning of no available vaccinations (not available type 1)        |
| 50000000008  | RSV - No RSV response as no active campaign (not available type 2)                                                                    |
| 50000000009  | RSV - Not Actionable despite to membership of an Age Cohort with reasoning of dose not yet due                                        |
| 50000000010  | RSV - Not Actionable despite to membership of an Age Cohort with reasoning of dose not far enough apart                               |
| 50000000011  | RSV - Not Actionable despite to membership of an Age Cohort with reasoning of vaccination given in current setting (e.g. care home)   |
| 50000000012  | RSV - Not Actionable despite no cohort membership with reasoning of already vaccinated (type 1 includes unknown cohort)               |
| 50000000013  | RSV - Not Actionable despite no cohort membership with reasoning of already vaccinated (type 2 includes no cohorts)                   |
| 50000000014  | RSV - Not Actionable despite no cohort membership with reasoning of already vaccinated (type 2 includes no cohorts)                   |
| 90000000400  | Invalid input data                                                                                                                    |
| 90000000404  | Person not found                                                                                                                      |
| 90000000422  | Unrecognised input data. (Unprocessable Content)                                                                                      |
| 90000000500  | Internal server error                                                                                                                 |

See [app.py](app.py) for current examples.

## Deployment of sandbox image to APIM AWS ECR repository

In order for our sandbox to be deployed correctly, both the specification for the sandbox and the accompanying backend
need to be deployed.

Instructions for creation and deployment of the sandbox specification can be found in the [specification README](/specification/README.md)

To deploy the sandbox Docker image to AWS ECR, we use Proxygen CLI as follows:

1. Run `make build-and-publish-sandbox-image` to build the sandbox image and publish to the docker ECR repository.
2. Run `proxygen instance deploy sandbox eligibility-signposting-api build/specification/sandbox/eligibility-signposting-api.yaml`
   to build and publish the sandbox spec to the sandbox instance on APIM.
