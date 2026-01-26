
#!/usr/bin/env bash
set -e

APIM_ENV_NAME="$1"

# Map APIM environment names to AWS account ID and environment name
case "$APIM_ENV_NAME" in
  dev)
    AWS_ENV_NAME="dev"
    EXPECTED_ACCOUNT="448049830832"
    ;;
  ptl)
    AWS_ENV_NAME="preprod" # Called 'preprod' in AWS and `ptl` in APIM
    EXPECTED_ACCOUNT="203918864209"
    ;;
  prod)
    AWS_ENV_NAME="prod"
    EXPECTED_ACCOUNT="333333333333"
    ;;
  *)
    echo "Unknown APIM environment: $APIM_ENV_NAME"
    exit 1
    ;;
esac

# Read the currently authenticated AWS account
CURRENT_ACCOUNT=$(aws sts get-caller-identity --query "Account" --output text)

# Compare the current account with the expected account
if [ "$CURRENT_ACCOUNT" != "$EXPECTED_ACCOUNT" ]; then
  echo "AWS account mismatch!"
#  MSG="The 'ENV' arg '$APIM_ENV_NAME' for APIM maps to the AWS env '$AWS_ENV_NAME' and account $EXPECTED_ACCOUNT, but the current AWS account is $CURRENT_ACCOUNT."
#  echo "$MSG"
#  echo "The 'ENV' arg $APIM_ENV_NAME for APIM maps to the AWS env $AWS_ENV_NAME and account $EXPECTED_ACCOUNT, but the current AWS account is $CURRENT_ACCOUNT."
#  echo "APIM environment : $APIM_ENV_NAME"
#  echo "Expected AWS environment: $AWS_ENV_NAME"
#  echo "Expected account: $EXPECTED_ACCOUNT"
#  echo "Actual account :  $CURRENT_ACCOUNT"
#  echo "The APIM '$APIM_ENV_NAME' environment is mapped to the AWS '$AWS_ENV_NAME' environment and account $EXPECTED_ACCOUNT, but the current AWS account is $CURRENT_ACCOUNT."
  echo "The expected mapping for the argument 'ENV=$APIM_ENV_NAME' is AWS '$AWS_ENV_NAME' account $EXPECTED_ACCOUNT, but the current AWS account is $CURRENT_ACCOUNT."
  echo "Please switch to the correct AWS account and try again."
  echo "Exiting script..."
  exit 1
fi

echo "Active login to AWS '$AWS_ENV_NAME' account $CURRENT_ACCOUNT verified."
