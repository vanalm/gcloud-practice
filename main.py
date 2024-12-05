import os
from flask import jsonify, request
# from twilio.rest import Client
import openai
# from google.cloud import secretmanager, storage
from dotenv import load_dotenv
# import json
import datetime
from datetime import datetime, timezone

from utils import get_LLM_response, send_message_via_twilio, access_secret, write_log_to_storage
import time
from twilio.request_validator import RequestValidator
import base64
import urllib.parse
from utils import (
    initialize_environment,
    get_LLM_response,
    send_message_via_twilio,
    access_secret,
    write_log_to_storage
)

# Load environment variables
load_dotenv()

# Determine environment
ENVIRONMENT = os.getenv('ENVIRONMENT', 'dev')  # Defaults to 'development'

# Initialize environment
initialize_environment()

def auto_responder(request):
    print(f'\n\n\nRequest: \n{request}')

    # Validate incoming request
    start = time.time()
    try:
        # Extract headers
        headers = request.headers
        print(f'\n\nHEADER RETRIEVED\n{headers}\n\n')
        twilio_signature = headers.get('X-Twilio-Signature', '')
        print(f'\nTwilio_signature: {twilio_signature}\n\n')
        #alternative way to get twilio signature
        # twilio_signature = next((value for key, value in headers.items() if key.lower() == 'x-twilio-signature'), None)
        # print(f'\nSecond twilio_signature: {twilio_signature}\n\n\n\n')
        # Get the full URL of the request

        # Reconstruct the full URL of the request
        forwarded_proto = request.headers.get('X-Forwarded-Proto', 'http')
        forwarded_host = request.headers.get('X-Forwarded-Host', request.host)
        url = f"{forwarded_proto}://{forwarded_host}{request.full_path}"
        # print(f"Reconstructed URL for validation: {url}")

        # Get POST parameters
        if request.content_type == 'application/json':
            params = request.get_json() or {}
        else:
            params = request.form.to_dict()  # For form data (application/x-www-form-urlencoded)
        print(f'params: {params}\n\n')
        # Twilio signature validation
        auth_token = TWILIO_AUTH_TOKEN  # Use the auth token retrieved earlier
        validator = RequestValidator(auth_token)
  
        if not validator.validate(url, params, twilio_signature):
            print("Twilio signature validation failed")
            return jsonify({'statusCode': 403, 'body': 'Invalid request.'}), 403

    except Exception as e:
        print(f'An error occurred: {e}')
        return jsonify({'statusCode': 500, 'body': 'Internal Server Error'}), 500

    print(f"VALIDATION TOOK {time.time() - start}")

    phone_number = params['From']
    message_body = params['Body']

    print(f'received message from {phone_number}: {message_body}')
    # setup content for llm request
    context = 'This is a test of a local system. pease provide terse response, body of which is just a haiku.'
    context = {'role': 'system', "content": context}
    current_message = {"role": "user", "content": message_body}
    # Get terse response from OpenAI
    llm_response = get_LLM_response([context, current_message])

    # Send response via Twilio
    msg_id = send_message_via_twilio(phone_number, llm_response, None)

    # Prepare log data

    log_data = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'from_number': TWILIO_PHONE_NUMBER,
        'to_number': phone_number,
        'incoming_message': message_body,
        'terse_response': llm_response,
        # 'message_sid': message.sid
    }
    

    # Write log to Cloud Storage
    write_log_to_storage(log_data)

    return jsonify({'status': 'Message sent'}), 200

