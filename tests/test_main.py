# tests/test_main.py

import pytest
from unittest.mock import patch, MagicMock
from flask import Flask, request
from main import auto_responder
from utils import TWILIO_AUTH_TOKEN
import os

# Sample data for tests
VALID_TWILIO_SIGNATURE = 'valid_signature'
INVALID_TWILIO_SIGNATURE = 'invalid_signature'
TEST_URL = 'http://testserver/'

@pytest.fixture(autouse=True)
def set_env():
    os.environ['ENVIRONMENT'] = 'test'

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app


def generate_twilio_request(data, headers):
    """Helper function to create a test request context."""
    with Flask(__name__).test_request_context(
        '/', method='POST', data=data, headers=headers
    ):
        yield request


@patch('main.get_LLM_response')
@patch('main.send_message_via_twilio')
@patch('main.write_log_to_storage')
@patch('main.RequestValidator')
def test_auto_responder_valid_request(
    mock_request_validator,
    mock_write_log,
    mock_send_message,
    mock_get_llm_response,
    app
):
    """
    Test auto_responder with a valid Twilio request.
    """

    # Arrange
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
        # Act
        response = auto_responder(request)

    # Assert
    assert response[1] == 200
    assert response[0].get_json() == {'status': 'Message sent'}
    mock_get_llm_response.assert_called_once()
    mock_send_message.assert_called_once_with('+1234567890', 'Mocked LLM response', None)
    mock_write_log.assert_called_once()
    mock_request_validator.return_value.validate.assert_called_once()


@patch('main.RequestValidator')
def test_auto_responder_invalid_signature(
    mock_request_validator,
    app
):
    """
    Test auto_responder with an invalid Twilio signature.
    """

    # Arrange
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
        # Act
        response = auto_responder(request)

    # Assert
    assert response[1] == 403
    assert response[0].get_json() == {
        'statusCode': 403,
        'body': 'Invalid request.'
    }
    mock_request_validator.return_value.validate.assert_called_once()


@patch('main.RequestValidator')
@patch('main.get_LLM_response')
def test_auto_responder_exception_handling(
    mock_get_llm_response,
    mock_request_validator,
    app
):
    """
    Test auto_responder handling an exception during processing.
    """

    # Arrange
    mock_request_validator.return_value = True
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
        # Act
        response = auto_responder(request)

    # Assert
    assert response[1] == 500
    assert response[0].get_json() == {
        'statusCode': 500,
        'body': 'Internal Server Error'
    }
