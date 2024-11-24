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

# Variables
PROJECT_ID=$(gcloud config get-value project)
REGION="us-west1"  # Replace with your actual region, e.g., us-central1

# Check if the function exists
if gcloud functions describe auto_responder --region="$REGION" >/dev/null 2>&1; 
then
  # Get the service account email associated with the Cloud Function
  SERVICE_ACCOUNT=$(gcloud functions describe auto_responder --region="$REGION" 
--format="value(serviceAccountEmail)")
else
  echo "Cloud Function 'auto_responder' not found. Using default service 
account."
  SERVICE_ACCOUNT="$PROJECT_ID@appspot.gserviceaccount.com"
fi

echo "Using service account: $SERVICE_ACCOUNT"

# Function to create secrets
create_secret() {
  SECRET_NAME=$1
  SECRET_VALUE=$2

  # Check if secret exists
  if gcloud secrets describe "$SECRET_NAME" >/dev/null 2>&1; then
    echo "Secret $SECRET_NAME already exists."
  else
    echo -n "$SECRET_VALUE" | gcloud secrets create "$SECRET_NAME" --data-file=-
    echo "Secret $SECRET_NAME created."
  fi
}

# Create secrets
create_secret TWILIO_AUTH_TOKEN "$TWILIO_AUTH_TOKEN"
create_secret OPENAI_API_KEY "$OPENAI_API_KEY"
create_secret TWILIO_ACCOUNT_SID "$TWILIO_ACCOUNT_SID"

# Grant access to the service account
grant_access() {
  SECRET_NAME=$1
  gcloud secrets add-iam-policy-binding "$SECRET_NAME" \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"
  echo "Granted access to $SECRET_NAME for $SERVICE_ACCOUNT."
}

grant_access TWILIO_AUTH_TOKEN
grant_access OPENAI_API_KEY
grant_access TWILIO_ACCOUNT_SID

echo "All secrets deployed and permissions granted."
#!/bin/bash

# Ensure the script exits on any error
set -e

# Load secrets from .env
export $(grep -v '^#' .env | xargs)

# Variables
PROJECT_ID=$(gcloud config get-value project)
SERVICE_ACCOUNT=$(gcloud functions describe auto_responder --format 'value(serviceAccountEmail)')

# Function to create secrets
create_secret() {
  SECRET_NAME=$1
  SECRET_VALUE=$2

  # Check if secret exists
  if gcloud secrets describe "$SECRET_NAME" >/dev/null 2>&1; then
    echo "Secret $SECRET_NAME already exists."
  else
    echo -n "$SECRET_VALUE" | gcloud secrets create "$SECRET_NAME" --data-file=-
    echo "Secret $SECRET_NAME created."
  fi
}

# Create secrets
create_secret TWILIO_AUTH_TOKEN "$TWILIO_AUTH_TOKEN"
create_secret OPENAI_API_KEY "$OPENAI_API_KEY"
create_secret TWILIO_ACCOUNT_SID "$TWILIO_ACCOUNT_SID"

# Grant access to the service account
grant_access() {
  SECRET_NAME=$1
  gcloud secrets add-iam-policy-binding "$SECRET_NAME" \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"
  echo "Granted access to $SECRET_NAME for $SERVICE_ACCOUNT."
}

grant_access TWILIO_AUTH_TOKEN
grant_access OPENAI_API_KEY
grant_access TWILIO_ACCOUNT_SID

echo "All secrets deployed and permissions granted."

