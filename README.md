# Practicing with GCloud: An SMS based chatbot

Setting up a system for local development and testing, and a CICD pipeline through Github actions. The app is A Python-based sms chatbot that integrates with Twilio, OpenAI's GPT model, and Google Cloud Platform (GCP) services. The application listens for incoming SMS messages, generates a response using OpenAI's API, 
sends the response back via Twilio, and logs the interaction to Google Cloud Storage. 

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Create and Activate a Virtual Environment](#2-create-and-activate-a-virtual-environment)
  - [3. Install Dependencies](#3-install-dependencies)
  - [4. Configure Environment Variables](#4-configure-environment-variables)
  - [5. Set Up Ngrok for Local Testing](#5-set-up-ngrok-for-local-testing)
  - [6. Update Twilio Webhook URL](#6-update-twilio-webhook-url)
- [Running the Application Locally](#running-the-application-locally)
- [Deploying to Google Cloud Functions](#deploying-to-google-cloud-functions)
  - [1. Enable Required GCP APIs](#1-enable-required-gcp-apis)
  - [2. Deploy the Cloud Function](#2-deploy-the-cloud-function)
  - [3. Update Twilio Webhook URL](#3-update-twilio-webhook-url)
- [Managing Secrets with Secret Manager](#managing-secrets-with-secret-manager)
  - [Using `deploy_secrets.sh`](#using-deploy_secretssh)
- [Logging to Google Cloud Storage](#logging-to-google-cloud-storage)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)
- [License](#license)

---

## Features

- **Twilio Integration**: Listens for incoming SMS messages using Twilio's webhook.
- **OpenAI Integration**: Generates responses using OpenAI's GPT model.
- **Google Cloud Functions**: Deployable as a serverless function.
- **Secret Management**: Uses Google Cloud Secret Manager to securely store API keys and tokens.
- **Logging**: Logs interactions to Google Cloud Storage for auditing and analysis.

## Prerequisites

- **Python 3.9+**
- **Google Cloud SDK (`gcloud` command-line tool)**
- **Twilio Account** with a registered phone number
- **OpenAI API Key**
- **Ngrok** (for local testing)
- **Google Cloud Project** with billing enabled
- **Google Cloud Storage Bucket** (for logging)
- **Google Cloud Secret Manager API Enabled**

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/auto_responder.git
cd auto_responder
```

### 2. Create and Activate a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory:

```bash
touch .env
```

Add the following environment variables to `.env`:

```dotenv
# .env file

# Environment
ENVIRONMENT=dev

# Twilio credentials
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_MESSAGING_SERVICE_SID=your_twilio_messaging_service_sid  # Optional if using Messaging Service
TWILIO_PHONE_NUMBER=your_twilio_phone_number  # E.g., +1234567890
TO_PHONE_NUMBER=your_phone_number_for_testing  # E.g., +1987654321

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key
```

**Note**: Replace placeholder values with your actual credentials. Do **NOT** commit `.env` to version 
control.

### 5. Set Up Ngrok for Local Testing

Download and install [Ngrok](https://ngrok.com/).

Start Ngrok to forward requests to your local server:

```bash
ngrok http 8080
```

Copy the forwarding URL provided by Ngrok (e.g., `https://abcd1234.ngrok.io`).

### 6. Update Twilio Webhook URL

In your Twilio Console:

1. Navigate to **Phone Numbers > Manage > Active Numbers**.
2. Click on your phone number.
3. Under **Messaging**, set the **Webhook** to your Ngrok URL:

   ```
   https://abcd1234.ngrok.io/auto_responder
   ```

4. Ensure the HTTP method is set to `POST`.

## Running the Application Locally

Run the application using the Functions Framework:

```bash
functions-framework --target auto_responder --debug
```

The application will be available at `http://localhost:8080/auto_responder`.

## Deploying to Google Cloud Functions

### 1. Enable Required GCP APIs

```bash
gcloud services enable cloudfunctions.googleapis.com secretmanager.googleapis.com storage.googleapis.com
```

### 2. Deploy the Cloud Function

```bash
gcloud functions deploy auto_responder \
  --runtime python39 \
  --trigger-http \
  --entry-point auto_responder \
  --region us-west1 \
  --service-account practice-dev-account@practice-dev-project.iam.gserviceaccount.com \
  --set-env-vars ENVIRONMENT=prod \
  --allow-unauthenticated
```

### 3. Update Twilio Webhook URL

After deployment, get the function's HTTPS endpoint:

```bash
gcloud functions describe auto_responder --region us-west1 --format='value(httpsTrigger.url)'
```

Set this URL as the Twilio webhook in the Twilio Console, similar to the local setup.

## Managing Secrets with Secret Manager

### Using `deploy_secrets.sh`

A script is provided to deploy secrets to Google Cloud Secret Manager and grant access to the Cloud 
Function's service account.

#### Steps:

1. Ensure the script is executable:

   ```bash
   chmod +x deploy_secrets.sh
   ```

2. Run the script:

   ```bash
   ./deploy_secrets.sh
   ```

   - The script reads secrets from your `.env` file.
   - It creates secrets in Secret Manager if they don't exist.
   - Grants `secretAccessor` role to the Cloud Function's service account.

## Logging to Google Cloud Storage

The application logs interactions by writing JSON files to a Google Cloud Storage bucket.

Ensure you have a bucket created:

```bash
gsutil mb -p your-project-id -l us-west1 gs://practice-dev-bucket/
```

Update the `BUCKET_NAMES` dictionary in `utils.py` if you have different bucket names.

## Testing

Send an SMS message to your Twilio phone number. The application should:

- Receive the message via the Twilio webhook.
- Generate a response using OpenAI's API.
- Send the response back to your phone via Twilio.
- Log the interaction to your Google Cloud Storage bucket.

## Troubleshooting

- **Authentication Errors**: Ensure your GCP credentials are set up correctly. Use `gcloud auth 
application-default login` for local testing.
- **Environment Variables**: Verify all required environment variables are set in the `.env` file.
- **Twilio Signature Validation Failed**: Check that the webhook URL in Twilio matches the URL constructed 
in the application.
- **OpenAI Errors**: Confirm your OpenAI API key is valid and has sufficient quota.
- **Permissions**: Ensure the service account has the necessary roles for Secret Manager and Cloud Storage.

## Security Considerations

- **Never Commit Sensitive Information**: Do not commit API keys, secrets, or `.env` files to version 
control.
- **Use Secret Manager**: Store secrets securely using Google Cloud Secret Manager.
- **Restrict Service Account Permissions**: Follow the principle of least privilege.

## License

This project is licensed under the MIT License.

---

**Disclaimer**: This README provides a concise overview of the setup and deployment process for the 
auto-responder application. Ensure you understand each step and modify configurations as needed for your 
specific use case.
