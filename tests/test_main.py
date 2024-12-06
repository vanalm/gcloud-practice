# tests/test_main.py

import pytest
from unittest.mock import patch, MagicMock, ANY
from flask import Flask, request
from main import auto_responder
import os

# Sample data for tests
VALID_TWILIO_SIGNATURE = 'valid_signature'
INVALID_TWILIO_SIGNATURE = 'invalid_signature'

@pytest.fixture(autouse=True)
def set_env():
    os.environ['ENVIRONMENT'] = 'test'

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app

def fake_env_vars():
    return {
        'environment': 'test',
        'TWILIO_ACCOUNT_SID': 'test_sid',
        'TWILIO_AUTH_TOKEN': 'test_auth_token',
        'TWILIO_PHONE_NUMBER': '+15555555555',
        'TO_PHONE_NUMBER': '+16666666666',
        'OPENAI_API_KEY': 'test_openai_key',
        'TWILIO_MESSAGING_SERVICE_SID': 'test_messaging_sid',
        'GCLOUD_DEV_KEY': 'test_gcloud_key',
        'BUCKET_NAME': 'practice-dev-bucket',
        'twilio_client': MagicMock(),
        'openai_client': MagicMock(),
        'storage_client': MagicMock()
    }

@patch('main.initialize_environment')
@patch('main.get_LLM_response')
@patch('main.send_message_via_twilio')
@patch('main.write_log_to_storage')
@patch('main.RequestValidator')
def test_auto_responder_valid_request(
    mock_request_validator,
    mock_write_log,
    mock_send_message,
    mock_get_llm_response,
    mock_initialize_environment,
    app
):
    mock_initialize_environment.return_value = fake_env_vars()
    mock_request_validator.return_value.validate.return_value = True
    mock_get_llm_response.return_value = 'Mocked LLM response'
    mock_send_message.return_value = 'mocked_message_id'
    mock_write_log.return_value = None

    data = {
        'From': '+1234567890',
        'Body': 'Hello'
    }
    headers = {
        'X-Twilio-Signature': VALID_TWILIO_SIGNATURE,
        'X-Forwarded-Proto': 'http',
        'X-Forwarded-Host': 'testserver'
    }

    with app.test_request_context('/', method='POST', data=data, headers=headers):
        response = auto_responder(request)

    assert response[1] == 200
    assert response[0].get_json() == {'status': 'Message sent'}

    # Check calls with updated signatures
    # The code in main calls get_LLM_response with [context, current_message], env_vars
    # 'context' and 'current_message' are built from the incoming message
    expected_context = {'role': 'system', 'content': 'This is a test of a local system. Please provide a terse response (a haiku).'}
    expected_message = {'role': 'user', 'content': 'Hello'}
    mock_get_llm_response.assert_called_once_with([expected_context, expected_message], mock_initialize_environment.return_value)

    # send_message_via_twilio is called with phone_number, llm_response, None, env_vars
    mock_send_message.assert_called_once_with('+1234567890', 'Mocked LLM response', None, mock_initialize_environment.return_value)

    # write_log_to_storage is called with log_data, env_vars
    mock_write_log.assert_called_once_with(ANY, mock_initialize_environment.return_value)

    # RequestValidator is called with TWILIO_AUTH_TOKEN from env_vars
    mock_request_validator.return_value.validate.assert_called_once()


@patch('main.initialize_environment')
@patch('main.RequestValidator')
def test_auto_responder_invalid_signature(
    mock_request_validator,
    mock_initialize_environment,
    app
):
    mock_initialize_environment.return_value = fake_env_vars()
    mock_request_validator.return_value.validate.return_value = False

    data = {
        'From': '+1234567890',
        'Body': 'Hello'
    }
    headers = {
        'X-Twilio-Signature': INVALID_TWILIO_SIGNATURE,
        'X-Forwarded-Proto': 'http',
        'X-Forwarded-Host': 'testserver'
    }

    with app.test_request_context('/', method='POST', data=data, headers=headers):
        response = auto_responder(request)

    assert response[1] == 403
    assert response[0].get_json() == {
        'statusCode': 403,
        'body': 'Invalid request.'
    }
    mock_request_validator.return_value.validate.assert_called_once()


@patch('main.initialize_environment')
@patch('main.get_LLM_response')
@patch('main.RequestValidator')
def test_auto_responder_exception_handling(
    mock_request_validator,
    mock_get_llm_response,
    mock_initialize_environment,
    app
):
    mock_initialize_environment.return_value = fake_env_vars()
    mock_request_validator.return_value.validate.return_value = True
    mock_get_llm_response.side_effect = Exception('Test exception')

    data = {
        'From': '+1234567890',
        'Body': 'Hello'
    }
    headers = {
        'X-Twilio-Signature': VALID_TWILIO_SIGNATURE,
        'X-Forwarded-Proto': 'http',
        'X-Forwarded-Host': 'testserver'
    }

    with app.test_request_context('/', method='POST', data=data, headers=headers):
        response = auto_responder(request)

    assert response[1] == 500
    assert response[0].get_json() == {
        'statusCode': 500,
        'body': 'Internal Server Error'
    }
