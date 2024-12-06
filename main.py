# main.py

import os
from flask import jsonify, request
import openai
from dotenv import load_dotenv
import datetime
from datetime import datetime, timezone
import time
import base64
import urllib.parse

from twilio.request_validator import RequestValidator
from utils import (
    initialize_environment,
    get_LLM_response,
    send_message_via_twilio,
    access_secret,
    write_log_to_storage
)

# Load environment variables from .env
load_dotenv()

def auto_responder(request):
    # Initialize environment inside the function, not at import time
    env_vars = initialize_environment()
    print(f' ENVVARS: {env_vars}')

    print(f'\n\n\nRequest: \n{request}')

    # Validate incoming request
    start = time.time()
    try:
        headers = request.headers
        print(f'\n\nHEADER RETRIEVED\n{headers}\n\n')
        twilio_signature = headers.get('X-Twilio-Signature', '')
        print(f'\nTwilio_signature: {twilio_signature}\n\n')

        # Reconstruct full URL
        forwarded_proto = request.headers.get('X-Forwarded-Proto', 'http')
        forwarded_host = request.headers.get('X-Forwarded-Host', request.host)
        url = f"{forwarded_proto}://{forwarded_host}{request.full_path}"

        # Get request parameters
        if request.content_type == 'application/json':
            params = request.get_json() or {}
        else:
            params = request.form.to_dict()
        print(f'params: {params}\n\n')

        # Validate Twilio signature
        auth_token = env_vars["TWILIO_AUTH_TOKEN"]
        validator = RequestValidator(auth_token)

        if not validator.validate(url, params, twilio_signature):
            print("Twilio signature validation failed")
            return jsonify({'statusCode': 403, 'body': 'Invalid request.'}), 403

    except Exception as e:
        print(f'An error occurred: {e}')
        return jsonify({'statusCode': 500, 'body': 'Internal Server Error'}), 500

    print(f"VALIDATION TOOK {time.time() - start}")

    phone_number = params.get('From')
    message_body = params.get('Body', '')

    print(f'received message from {phone_number}: {message_body}')

    # Prepare content for LLM request
    context = {'role': 'system', "content": 'This is a test of a local system. Please provide a terse response (a haiku).'}
    current_message = {"role": "user", "content": message_body}

    # Get response from LLM
    llm_response = get_LLM_response([context, current_message], env_vars)

    # Send response via Twilio
    msg_id = send_message_via_twilio(phone_number, llm_response, None, env_vars)

    # Prepare log data
    log_data = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'from_number': env_vars['TWILIO_PHONE_NUMBER'],
        'to_number': phone_number,
        'incoming_message': message_body,
        'terse_response': llm_response,
    }

    # Write log to Cloud Storage
    write_log_to_storage(log_data, env_vars)

    return jsonify({'status': 'Message sent'}), 200
