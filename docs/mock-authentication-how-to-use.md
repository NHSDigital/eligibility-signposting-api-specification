# Mock Authentication Script: How To Use

This guide shows how to use the command line tool in [scripts/mock-authentication.py](../scripts/mock-authentication.py) to:

- generate RSA keys and JWKS,
- fetch an OAuth2 access token,
- call an API endpoint with JWT-based app-restricted auth.

## What this script does

The script automates the JWT client assertion flow used by NHS application-restricted APIs:

1. Creates an RSA key pair.
2. Generates a JWKS document from the public key.
3. Signs a JWT assertion with the private key.
4. Exchanges the assertion for an access token.
5. Calls an API using `Authorization: Bearer <token>`.

## Prerequisites

- Python 3.10+ (or compatible Python 3 version).
- A valid NHS API key from the developer portal.
- Your public key uploaded to the portal (or hosted JWKS URL configured for your app).

Install required Python packages:

```bash
pip install "PyJWT[crypto]" requests cryptography
```

## Script location

From repository root:

```bash
python3 scripts/mock-authentication.py --help
```

## Commands overview

```bash
python3 scripts/mock-authentication.py <command> [options]
```

Available commands:

- `generate-keys` - Generate a private key, public key, and JWKS file.
- `get-token` - Generate a JWT and exchange it for an access token.
- `call-api` - Call an API endpoint using the access token.

## 1) Generate keys and JWKS

Generate a key pair and JWKS for integration environment:

```bash
python3 scripts/mock-authentication.py generate-keys \
  --api-key YOUR_API_KEY \
  --env int \
  --output-dir ./.auth
```

Outputs:

- `./.auth/int-1.pem` (private key)
- `./.auth/int-1.pem.pub` (public key)
- `./.auth/int-1.json` (JWKS)

Use a custom key ID:

```bash
python3 scripts/mock-authentication.py generate-keys \
  --api-key YOUR_API_KEY \
  --env int \
  --kid my-int-key-01 \
  --output-dir ./.auth
```

## 2) Get an access token

```bash
python3 scripts/mock-authentication.py get-token \
  --api-key YOUR_API_KEY \
  --env int \
  --private-key ./.auth/int-1.pem
```

Use `--kid` if you used a non-default KID:

```bash
python3 scripts/mock-authentication.py get-token \
  --api-key YOUR_API_KEY \
  --env int \
  --kid my-int-key-01 \
  --private-key ./.auth/my-int-key-01.pem
```

If `--kid` is omitted, the script now derives KID from the private key filename when it ends with `.pem`.
For example, using `--private-key ./.auth/my-int-key-01.pem` will use `my-int-key-01` automatically.

## 3) Call an API endpoint

Basic GET call:

```bash
python3 scripts/mock-authentication.py call-api \
  --api-key YOUR_API_KEY \
  --env int \
  --private-key ./.auth/int-1.pem \
  --url https://int.api.service.nhs.uk/eligibility-signposting-api/patient-check/123
```

GET call including NHS number header and product ID header:

```bash
python3 scripts/mock-authentication.py call-api \
  --api-key YOUR_API_KEY \
  --env int \
  --private-key ./.auth/int-1.pem \
  --url https://int.api.service.nhs.uk/eligibility-signposting-api/patient-check/123 \
  --nhs-number 1234567890
```

Call with extra headers:

```bash
python3 scripts/mock-authentication.py call-api \
  --api-key YOUR_API_KEY \
  --env int \
  --private-key ./.auth/int-1.pem \
  --url https://int.api.service.nhs.uk/some-api/endpoint \
  --header "X-Correlation-ID: 7d8ff2e8-6a69-4cbe-a0f3-6f67e6fc2f91" \
  --header "Accept: application/json"
```

Use another HTTP method:

```bash
python3 scripts/mock-authentication.py call-api \
  --api-key YOUR_API_KEY \
  --env int \
  --private-key ./.auth/int-1.pem \
  --method POST \
  --url https://int.api.service.nhs.uk/some-api/endpoint \
  --header "Content-Type: application/json"
```

## Environment options

- `generate-keys` and `get-token` support: `dev`, `int`, `prod`
- `call-api` supports: `dev`, `int`, `prod`, `sandbox`

Note about `sandbox`:

- For `call-api --env sandbox`, the script still uses the `int` OAuth token endpoint for token generation internally.
- This is how the current script is implemented.

## Typical end-to-end workflow

```bash
# 1) Generate keys and JWKS
python3 scripts/mock-authentication.py generate-keys \
  --api-key YOUR_API_KEY \
  --env int \
  --output-dir ./.auth

# 2) Upload or host JWKS (manual step)
#    File to publish: ./.auth/int-1.json

# 3) Call target API
python3 scripts/mock-authentication.py call-api \
  --api-key YOUR_API_KEY \
  --env int \
  --private-key ./.auth/int-1.pem \
  --url https://int.api.service.nhs.uk/eligibility-signposting-api/patient-check/123 \
  --nhs-number 1234567890
```

## Troubleshooting

### Missing dependencies

If you see `Missing required dependencies`, run:

```bash
pip install "PyJWT[crypto]" requests cryptography
```

### Invalid environment

If you see an invalid environment error, check command-specific supported values:

- `generate-keys`, `get-token`: `dev|int|prod`
- `call-api`: `dev|int|prod|sandbox`

### Token request fails (401/403)

Check:

- API key is correct.
- JWKS in portal matches the private key used by the script.
- KID (`--kid`) matches what is configured.
- System clock is in sync (JWTs are short-lived).

### Invalid header format warning

`--header` values must use this format:

```text
"Header-Name: value"
```

## Security notes

- Never commit private keys (`*.pem`) to source control.
- Store private keys in a secure location and rotate them periodically.
- Treat access tokens as secrets.
