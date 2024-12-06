# tests/test_utils.py

import os
import pytest
from unittest.mock import patch, MagicMock
from utils import (
    initialize_environment,
    get_LLM_response,
    send_message_via_twilio,
    write_log_to_storage,
    access_secret
)
import uuid

@pytest.fixture(autouse=True)
def set_env():
    os.environ['ENVIRONMENT'] = 'test'
    os.environ['TWILIO_ACCOUNT_SID'] = 'test_account_sid'
    os.environ['TWILIO_AUTH_TOKEN'] = 'test_auth_token'
    os.environ['TWILIO_PHONE_NUMBER'] = 'test_twilio_phone_number'
    os.environ['TO_PHONE_NUMBER'] = 'test_to_phone_number'
    os.environ['OPENAI_API_KEY'] = 'test_openai_key'
    os.environ['TWILIO_MESSAGING_SERVICE_SID'] = 'test_messaging_service_sid'

@pytest.fixture(scope="module")
def env_vars():
    return initialize_environment()

@patch('utils.openai_client.chat.completions.create')
def test_get_LLM_response_success(mock_openai_create, env_vars):
    # Arrange
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content='Mocked LLM response'))]
    mock_openai_create.return_value = mock_response
    content = [{'role': 'user', 'content': 'Hello'}]

    # Act
    response = get_LLM_response(content, env_vars)

    # Assert
    assert response == 'Mocked LLM response'
    mock_openai_create.assert_called_once()


@patch('utils.openai_client.chat.completions.create')
def test_get_LLM_response_exception(mock_openai_create, env_vars):
    # Arrange
    mock_openai_create.side_effect = Exception('OpenAI API error')
    content = [{'role': 'user', 'content': 'Hello'}]

    # Act
    response = get_LLM_response(content, env_vars)

    # Assert
    assert response is None
    mock_openai_create.assert_called_once()


@patch('utils.Client')
def test_send_message_via_twilio_success(mock_twilio_client, env_vars):
    # Arrange
    mock_twilio_client.return_value.messages.create.return_value.sid = 'mocked_sid'
    phone_number = '+1234567890'
    message_body = 'Test message'
    session_id = None

    # Act
    unique_id = send_message_via_twilio(phone_number, message_body, session_id, env_vars)

    # Assert
    assert unique_id is not None
    mock_twilio_client.return_value.messages.create.assert_called_once_with(
        messaging_service_sid='test_messaging_service_sid',
        from_='test_twilio_phone_number',
        body=message_body,
        to=phone_number
    )


@patch('utils.Client')
def test_send_message_via_twilio_exception(mock_twilio_client, env_vars):
    # Arrange
    mock_twilio_client.return_value.messages.create.side_effect = Exception('Twilio API error')
    phone_number = '+1234567890'
    message_body = 'Test message'
    session_id = None

    # Act
    unique_id = send_message_via_twilio(phone_number, message_body, session_id, env_vars)

    # Assert
    assert unique_id is None
    mock_twilio_client.return_value.messages.create.assert_called_once()


@patch('utils.storage.Client')
def test_write_log_to_storage_success(mock_storage_client, env_vars):
    # Arrange
    mock_bucket = mock_storage_client.return_value.bucket.return_value
    mock_blob = mock_bucket.blob.return_value
    mock_blob.upload_from_string.return_value = None
    log_data = {'test': 'data'}

    # Act
    result = write_log_to_storage(log_data, env_vars)

    # Assert
    assert result is None
    mock_storage_client.return_value.bucket.assert_called_once_with(env_vars['BUCKET_NAME'])
    mock_bucket.blob.assert_called()
    mock_blob.upload_from_string.assert_called_once()


@patch('utils.storage.Client')
def test_write_log_to_storage_exception(mock_storage_client, env_vars):
    # Arrange
    mock_bucket = mock_storage_client.return_value.bucket.return_value
    mock_bucket.blob.side_effect = Exception('Storage error')
    log_data = {'test': 'data'}

    # Act
    result = write_log_to_storage(log_data, env_vars)

    # Assert
    assert result is None
    mock_storage_client.return_value.bucket.assert_called_once()


@patch('utils.secretmanager.SecretManagerServiceClient')
def test_access_secret_success(mock_secret_client, env_vars):
    # Arrange
    mock_response = MagicMock()
    mock_response.payload.data.decode.return_value = 'secret_value'
    mock_secret_client.return_value.access_secret_version.return_value = mock_response

    # Act
    secret = access_secret('TEST_SECRET', env_vars)

    # Assert
    assert secret == 'secret_value'
    mock_secret_client.return_value.access_secret_version.assert_called_once()


@patch('utils.secretmanager.SecretManagerServiceClient')
def test_access_secret_exception(mock_secret_client, env_vars):
    # Arrange
    mock_secret_client.return_value.access_secret_version.side_effect = Exception('Secret Manager error')

    # Act
    secret = access_secret('TEST_SECRET', env_vars)

    # Assert
    assert secret is None
    mock_secret_client.return_value.access_secret_version.assert_called_once()
