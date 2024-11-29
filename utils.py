from openai import OpenAI
import json
from twilio.rest import Client
from google.cloud import secretmanager, storage
import os
from dotenv import load_dotenv
from dotenv import load_dotenv
import datetime
from datetime import datetime, timezone
import uuid


print("this is the new version of utils.py")
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


try:
    # Load credentials based on the running environment
    if os.getenv('CI'):  # Detect GitHub Actions
        print("Running in GitHub Actions...")
        environment = 'dev'  # Default to development for CI
        print(f'environment: {environment}')
        TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
        print(f'got TWILIO_ACCOUNT_SID: {TWILIO_ACCOUNT_SID}')
        TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
        print(f'got AUTH: {TWILIO_AUTH_TOKEN}')  
        TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
        print(f'got t-phone:')
        TO_PHONE_NUMBER = os.getenv("TO_PHONE_NUMBER")
        print(f'got To phone:')
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        print(f'got TWILIO_ACCOUNT_SID:')
        TWILIO_MESSAGING_SERVICE_SID = os.getenv("TWILIO_MESSAGING_SERVICE_SID")
        print(f'got TWILIO_ACCOUNT_SID:')
        GCLOUD_DEV_KEY = os.getenv("GCLOUD_DEV_KEY")
        print(f'got TWILIO_ACCOUNT_SID:')

    elif os.getenv('FUNCTION_NAME'):  # Detect Google Cloud
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
        environment = 'dev'  # Default to development for local testing
        load_dotenv()
        TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
        TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
        TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
        TO_PHONE_NUMBER = os.getenv("TO_PHONE_NUMBER")
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        TWILIO_MESSAGING_SERVICE_SID = os.getenv("TWILIO_MESSAGING_SERVICE_SID")

    # # Verify secrets are loaded
    # required_secrets = [
    #     TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER,
    #     TO_PHONE_NUMBER, OPENAI_API_KEY, TWILIO_MESSAGING_SERVICE_SID
    # ]
    # if not all(required_secrets):
    #     raise ValueError("One or more required secrets are missing.")

    # Bucket names per environment
    BUCKET_NAMES = {
        'dev': 'practice-dev-bucket',
        'prod': 'practice-prod-bucket'
    }

    BUCKET_NAME = BUCKET_NAMES.get(environment)
    print(f"Using bucket: {BUCKET_NAME}")

except Exception as e:
    print(f"Error during initialization: {e}")
    raise 


# Initialize clients
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
openai_client = OpenAI()
openai_client.api_key = OPENAI_API_KEY
storage_client = storage.Client()



print("random line in utils")
def get_LLM_response(content):

    # print(f'Making OpenAI API request... with payload:\n{content}')
    try:

        completion = openai_client.chat.completions.create(
            # model="gpt-4o-mini",
            model="gpt-4o",
            messages=content,
            max_tokens = 500,

        )

        
        return completion.choices[0].message.content
    except Exception as e:
        print(f"error contacting openai: {e}")
        
        return None
    

def send_message_via_twilio(phone_number, message_body, session_id):
    """
    Send a message via the Twilio API and saves relevant details for status callback and session.

    Parameters:
        phone_number (str): The recipient's phone number.
        message_body (str): The body of the message to be sent.

    Returns:
        str: The unique_id used for identifying the message or None if sending fails.
    """
    unique_id = str(uuid.uuid4())

    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            messaging_service_sid=TWILIO_MESSAGING_SERVICE_SID,
            from_=TWILIO_PHONE_NUMBER,
            body=message_body,
            to=phone_number
            # status_callback=f'https://3ia7ku3dozymdbodomst2ht6ny0cdpuo.lambda-url.us-west-2.on.aws/?unique_id={unique_id}'
        )
        
        print(f'Sent message:\n {message_body}\n to {phone_number} with UUID {unique_id}')
    except Exception as e:
        print(f"Error sending message via Twilio API: {e}")
        return None

    # try:
    #     save_response_to_pending(session_id, phone_number, message_body, unique_id)
    # except Exception as e:
    #     print(f"Error storing message in user session: {e}")

    return unique_id

def access_secret(secret_name):
    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.environ.get('GCP_PROJECT')
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(name=name)
        return response.payload.data.decode('UTF-8')
    except Exception as e:
        print(f"Error accessing secret: {e}")
        return None

def write_log_to_storage(log_data):
    try:
        print(f'setting up storage client...')
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)  # Replace with your bucket name
        timestamp = datetime.now(timezone.utc).isoformat(),
        blob = bucket.blob(f'logs/{timestamp}.json')
        blob.upload_from_string(
            data=json.dumps(log_data),
            content_type='application/json'
        )
        print(f'Log written to Cloud Storage: {log_data}')
    except Exception as e:
        print(f"Error writing log to Cloud Storage: {e}")
        return None