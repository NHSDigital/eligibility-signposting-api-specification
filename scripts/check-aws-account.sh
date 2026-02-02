
#!/usr/bin/env bash
set -e

APIM_ENV_NAME="$1"

# Expected AWS account for dev environment
EXPECTED_ACCOUNT="448049830832"

# Read the currently authenticated AWS account
CURRENT_ACCOUNT=$(aws sts get-caller-identity --query "Account" --output text)

# Compare the current account with the expected account
if [ "$CURRENT_ACCOUNT" != "$EXPECTED_ACCOUNT" ]; then
  echo "AWS account mismatch!"
  echo "The expected login is AWS '$APIM_ENV_NAME' account $EXPECTED_ACCOUNT, but the current logged in AWS account is $CURRENT_ACCOUNT."
  echo "Please switch to the correct AWS account and try again."
  echo "Exiting script..."
  exit 1
fi

echo "Active login to AWS '$APIM_ENV_NAME' account $CURRENT_ACCOUNT verified."
