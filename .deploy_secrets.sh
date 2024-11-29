#!/bin/bash

# Ensure the script exits on any error
set -e

# Load secrets from .env
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
else
  echo ".env file not found!"
  exit 1
fi

# Define project and service account for dev
PROJECT_ID="practice-dev-project"  # Replace with your dev project ID
SERVICE_ACCOUNT="practice-dev-account@practice-dev-project.iam.gserviceaccount.com"

# Echo details for verification
echo "Using project: $PROJECT_ID"
echo "Using service account: $SERVICE_ACCOUNT"

# Function to create secrets
create_secret() {
  SECRET_NAME=$1
  SECRET_VALUE=$2

  # Check if secret exists
  if gcloud secrets describe "$SECRET_NAME" --project="$PROJECT_ID" >/dev/null 2>&1; then
    echo "Secret $SECRET_NAME already exists in $PROJECT_ID."
  else
    echo -n "$SECRET_VALUE" | gcloud secrets create "$SECRET_NAME" --data-file=- --project="$PROJECT_ID"
    echo "Secret $SECRET_NAME created in $PROJECT_ID."
  fi
}

# Push all secrets from .env
create_secret TWILIO_ACCOUNT_SID "$TWILIO_ACCOUNT_SID"
create_secret TWILIO_AUTH_TOKEN "$TWILIO_AUTH_TOKEN"
create_secret TWILIO_PHONE_NUMBER "$TWILIO_PHONE_NUMBER"
create_secret TO_PHONE_NUMBER "$TO_PHONE_NUMBER"
create_secret OPENAI_API_KEY "$OPENAI_API_KEY"
create_secret TWILIO_MESSAGING_SERVICE_SID "$TWILIO_MESSAGING_SERVICE_SID"

# Grant access to the service account for all secrets
grant_access() {
  SECRET_NAME=$1
  gcloud secrets add-iam-policy-binding "$SECRET_NAME" \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor" \
    --project="$PROJECT_ID"
  echo "Granted access to $SECRET_NAME for $SERVICE_ACCOUNT in $PROJECT_ID."
}

grant_access TWILIO_ACCOUNT_SID
grant_access TWILIO_AUTH_TOKEN
grant_access TWILIO_PHONE_NUMBER
grant_access TO_PHONE_NUMBER
grant_access OPENAI_API_KEY
grant_access TWILIO_MESSAGING_SERVICE_SID

echo "All secrets deployed and permissions granted for dev."
