from openai import OpenAI
import json
from twilio.rest import Client
from google.cloud import secretmanager, storage
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
import uuid

def get_secret(secret_name):
    """Retrieve secret from Google Cloud Secret Manager."""
    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.getenv('GCLOUD_PROJECT')
        if not project_id:
            raise ValueError("GCLOUD_PROJECT environment variable is not set.")
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(name=name)
        return response.payload.data.decode('UTF-8')
    except Exception as e:
        raise RuntimeError(f"Failed to retrieve secret '{secret_name}': {e}")

def initialize_environment():
    """Initialize environment variables and clients, returning them in a dictionary."""
    try:
        if os.getenv('CI'):  # Running in GitHub Actions
            print("Running in GitHub Actions...")
            environment = 'dev'
            TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
            TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
            TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
            TO_PHONE_NUMBER = os.getenv("TO_PHONE_NUMBER")
            OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
            TWILIO_MESSAGING_SERVICE_SID = os.getenv("TWILIO_MESSAGING_SERVICE_SID")
            GCLOUD_DEV_KEY = os.getenv("GCLOUD_DEV_KEY")

        elif os.getenv('FUNCTION_NAME'):  # Running in Google Cloud Functions
            print("Running in Google Cloud...")
            project_id = os.getenv('GCLOUD_PROJECT')
            if not project_id:
                raise ValueError("GCLOUD_PROJECT environment variable is not set in GCP.")

            environment = 'prod' if project_id.endswith('-prod') else 'dev'
            TWILIO_ACCOUNT_SID = get_secret("TWILIO_ACCOUNT_SID")
            TWILIO_AUTH_TOKEN = get_secret("TWILIO_AUTH_TOKEN")
            TWILIO_PHONE_NUMBER = get_secret("TWILIO_PHONE_NUMBER")
            TO_PHONE_NUMBER = get_secret("TO_PHONE_NUMBER")
            OPENAI_API_KEY = get_secret("OPENAI_API_KEY")
            TWILIO_MESSAGING_SERVICE_SID = get_secret("TWILIO_MESSAGING_SERVICE_SID")
            GCLOUD_DEV_KEY = os.getenv("GCLOUD_DEV_KEY")

        else:  # Local development
            print("Running locally...")
            environment = 'dev'
            load_dotenv()
            TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
            TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
            TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
            TO_PHONE_NUMBER = os.getenv("TO_PHONE_NUMBER")
            OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
            TWILIO_MESSAGING_SERVICE_SID = os.getenv("TWILIO_MESSAGING_SERVICE_SID")
            GCLOUD_DEV_KEY = os.getenv("GCLOUD_DEV_KEY")

        BUCKET_NAMES = {
            'dev': 'practice-dev-bucket',
            'prod': 'practice-prod-bucket'
        }
        BUCKET_NAME = BUCKET_NAMES.get(environment)

        print(f"Using bucket: {BUCKET_NAME}")
        print("Initializing clients...")
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        openai_client = OpenAI()
        openai_client.api_key = OPENAI_API_KEY
        storage_client = storage.Client()

        # Initialize a mockable secret manager client here if needed
        # For testing, we'll allow env_vars to be overridden
        secretmanager_client = secretmanager.SecretManagerServiceClient()

        env_vars = {
            'environment': environment,
            'TWILIO_ACCOUNT_SID': TWILIO_ACCOUNT_SID,
            'TWILIO_AUTH_TOKEN': TWILIO_AUTH_TOKEN,
            'TWILIO_PHONE_NUMBER': TWILIO_PHONE_NUMBER,
            'TO_PHONE_NUMBER': TO_PHONE_NUMBER,
            'OPENAI_API_KEY': OPENAI_API_KEY,
            'TWILIO_MESSAGING_SERVICE_SID': TWILIO_MESSAGING_SERVICE_SID,
            'GCLOUD_DEV_KEY': GCLOUD_DEV_KEY,
            'BUCKET_NAME': BUCKET_NAME,
            'twilio_client': twilio_client,
            'openai_client': openai_client,
            'storage_client': storage_client,
            'secretmanager_client': secretmanager_client,
            'GCLOUD_PROJECT': os.getenv('GCLOUD_PROJECT', 'test_project')  # fallback for tests
        }

        return env_vars

    except Exception as e:
        print(f"Error during initialization: {e}")
        raise

def get_LLM_response(content, env_vars):
    openai_client = env_vars['openai_client']
    try:
        completion = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=content,
            max_tokens=500,
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error contacting OpenAI: {e}")
        return None

def send_message_via_twilio(phone_number, message_body, session_id, env_vars):
    print(f'TWILIO SEND ENVVARS: {env_vars}')
    twilio_client = env_vars['twilio_client']
    messaging_service_sid = env_vars['TWILIO_MESSAGING_SERVICE_SID']
    from_number = env_vars['TWILIO_PHONE_NUMBER']

    unique_id = str(uuid.uuid4())
    try:
        message = twilio_client.messages.create(
            messaging_service_sid=messaging_service_sid,
            from_=from_number,
            body=message_body,
            to=phone_number
        )
        print(f'Sent message:\n {message_body}\n to {phone_number} with UUID {unique_id}')
    except Exception as e:
        print(f"Error sending message via Twilio API: {e}")
        return None

    return unique_id

def access_secret(secret_name, env_vars):
    try:
        client = env_vars['secretmanager_client']
        project_id = env_vars.get('GCLOUD_PROJECT', 'test_project')
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(name=name)
        return response.payload.data.decode('UTF-8')
    except Exception as e:
        print(f"Error accessing secret: {e}")
        return None

def write_log_to_storage(log_data, env_vars):
    try:
        storage_client = env_vars['storage_client']
        bucket_name = env_vars['BUCKET_NAME']
        bucket = storage_client.bucket(bucket_name)
        timestamp = datetime.now(timezone.utc).isoformat()
        blob = bucket.blob(f'logs/{timestamp}.json')
        blob.upload_from_string(
            data=json.dumps(log_data),
            content_type='application/json'
        )
        print(f'Log written to Cloud Storage: {log_data}')
    except Exception as e:
        print(f"Error writing log to Cloud Storage: {e}")
        return None
