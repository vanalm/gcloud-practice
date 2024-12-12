# tests/test_utils.py

import os
import pytest
from unittest.mock import MagicMock
from utils import (
    get_LLM_response,
    send_message_via_twilio,
    write_log_to_storage,
    access_secret
)
import uuid

@pytest.fixture(autouse=True)
def set_env():
    # Set some environment variables if needed
    # These are mostly placeholders since we're using mocks in env_vars
    os.environ['ENVIRONMENT'] = 'test'
    os.environ['TWILIO_ACCOUNT_SID'] = 'test_account_sid'
    os.environ['TWILIO_AUTH_TOKEN'] = 'test_auth_token'
    os.environ['TWILIO_PHONE_NUMBER'] = 'test_twilio_phone_number'
    os.environ['TO_PHONE_NUMBER'] = 'test_to_phone_number'
    os.environ['OPENAI_API_KEY'] = 'test_openai_key'
    os.environ['TWILIO_MESSAGING_SERVICE_SID'] = 'test_messaging_service_sid'

@pytest.fixture(scope="function")
def env_vars():
    # Return a dictionary of environment variables and pre-mocked clients
    # Ensure your source code uses these mocks instead of creating new clients
    return {
        'environment': 'test',
        'TWILIO_ACCOUNT_SID': 'test_account_sid',
        'TWILIO_AUTH_TOKEN': 'test_auth_token',
        'TWILIO_PHONE_NUMBER': 'test_twilio_phone_number',
        'TO_PHONE_NUMBER': 'test_to_phone_number',
        'OPENAI_API_KEY': 'test_openai_key',
        'TWILIO_MESSAGING_SERVICE_SID': 'test_messaging_service_sid',
        'GCLOUD_DEV_KEY': 'test_gcloud_key',
        'BUCKET_NAME': 'test_bucket',
        'twilio_client': MagicMock(),
        'openai_client': MagicMock(),
        'storage_client': MagicMock(),
        'secretmanager_client': MagicMock()
    }

def test_get_LLM_response_success(env_vars):
    # Arrange
    mock_create = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content='Mocked LLM response'))]
    mock_create.return_value = mock_response
    env_vars['openai_client'].chat.completions.create = mock_create

    content = [{'role': 'user', 'content': 'Hello'}]

    # Act
    response = get_LLM_response(content, env_vars)

    # Assert
    assert response == 'Mocked LLM response'
    mock_create.assert_called_once()

def test_get_LLM_response_exception(env_vars):
    # Arrange
    mock_create = MagicMock(side_effect=Exception('OpenAI API error'))
    env_vars['openai_client'].chat.completions.create = mock_create

    content = [{'role': 'user', 'content': 'Hello'}]

    # Act
    response = get_LLM_response(content, env_vars)

    # Assert
    assert response is None
    mock_create.assert_called_once()

def test_send_message_via_twilio_success(env_vars):
    # Arrange
    env_vars['twilio_client'].messages.create.return_value.sid = 'mocked_sid'
    phone_number = '+1234567890'
    message_body = 'Test message'
    session_id = None

    # Act
    unique_id = send_message_via_twilio(phone_number, message_body, session_id, env_vars)

    # Assert
    assert unique_id is not None
    env_vars['twilio_client'].messages.create.assert_called_once_with(
        messaging_service_sid='test_messaging_service_sid',
        from_='test_twilio_phone_number',
        body=message_body,
        to=phone_number
    )

def test_send_message_via_twilio_exception(env_vars):
    # Arrange
    env_vars['twilio_client'].messages.create.side_effect = Exception('Twilio API error')
    phone_number = '+1234567890'
    message_body = 'Test message'
    session_id = None

    # Act
    unique_id = send_message_via_twilio(phone_number, message_body, session_id, env_vars)

    # Assert
    assert unique_id is None
    env_vars['twilio_client'].messages.create.assert_called_once()

def test_write_log_to_storage_success(env_vars):
    # Arrange
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    mock_bucket.blob.return_value = mock_blob
    env_vars['storage_client'].bucket.return_value = mock_bucket

    log_data = {'test': 'data'}

    # Act
    result = write_log_to_storage(log_data, env_vars)

    # Assert
    assert result is None
    env_vars['storage_client'].bucket.assert_called_once_with(env_vars['BUCKET_NAME'])
    mock_bucket.blob.assert_called()
    mock_blob.upload_from_string.assert_called_once()

def test_write_log_to_storage_exception(env_vars):
    # Arrange
    mock_bucket = MagicMock()
    mock_bucket.blob.side_effect = Exception('Storage error')
    env_vars['storage_client'].bucket.return_value = mock_bucket

    log_data = {'test': 'data'}

    # Act
    result = write_log_to_storage(log_data, env_vars)

    # Assert
    assert result is None
    env_vars['storage_client'].bucket.assert_called_once()

def test_access_secret_success(env_vars):
    # Arrange
    mock_response = MagicMock()
    mock_response.payload.data.decode.return_value = 'secret_value'
    env_vars['secretmanager_client'].access_secret_version.return_value = mock_response

    # Act
    secret = access_secret('TEST_SECRET', env_vars)

    # Assert
    assert secret == 'secret_value'
    env_vars['secretmanager_client'].access_secret_version.assert_called_once()

def test_access_secret_exception(env_vars):
    # Arrange
    env_vars['secretmanager_client'].access_secret_version.side_effect = Exception('Secret Manager error')

    # Act
    secret = access_secret('TEST_SECRET', env_vars)

    # Assert
    assert secret is None
    env_vars['secretmanager_client'].access_secret_version.assert_called_once()
