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

@pytest.fixture(scope="module", autouse=True)
def setup_environment():
    initialize_environment()
    
@patch('utils.openai_client.chat.completions.create')
def test_get_LLM_response_success(mock_openai_create):
    """
    Test get_LLM_response when OpenAI API call is successful.
    """

    # Arrange
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='Mocked LLM response'))
    ]
    mock_openai_create.return_value = mock_response
    content = [{'role': 'user', 'content': 'Hello'}]

    # Act
    response = get_LLM_response(content)

    # Assert
    assert response == 'Mocked LLM response'
    mock_openai_create.assert_called_once()


@patch('utils.openai_client.chat.completions.create')
def test_get_LLM_response_exception(mock_openai_create):
    """
    Test get_LLM_response when OpenAI API call raises an exception.
    """

    # Arrange
    mock_openai_create.side_effect = Exception('OpenAI API error')
    content = [{'role': 'user', 'content': 'Hello'}]

    # Act
    response = get_LLM_response(content)

    # Assert
    assert response is None
    mock_openai_create.assert_called_once()


@patch('utils.TWILIO_MESSAGING_SERVICE_SID', 'test_messaging_service_sid')
@patch('utils.TWILIO_PHONE_NUMBER', 'test_twilio_phone_number')
@patch('utils.Client')
def test_send_message_via_twilio_success(mock_twilio_client):
    """
    Test send_message_via_twilio when message is sent successfully.
    """

    # Arrange
    mock_twilio_client.return_value.messages.create.return_value.sid = 'mocked_sid'
    phone_number = '+1234567890'
    message_body = 'Test message'
    session_id = None

    # Act
    unique_id = send_message_via_twilio(phone_number, message_body, session_id)

    # Assert
    assert unique_id is not None
    mock_twilio_client.return_value.messages.create.assert_called_once_with(
        messaging_service_sid='test_messaging_service_sid',
        from_='test_twilio_phone_number',
        body=message_body,
        to=phone_number
    )


@patch('utils.Client')
def test_send_message_via_twilio_exception(mock_twilio_client):
    """
    Test send_message_via_twilio when Twilio API raises an exception.
    """

    # Arrange
    mock_twilio_client.return_value.messages.create.side_effect = Exception('Twilio API error')
    phone_number = '+1234567890'
    message_body = 'Test message'
    session_id = None

    # Act
    unique_id = send_message_via_twilio(phone_number, message_body, session_id)

    # Assert
    assert unique_id is None
    mock_twilio_client.return_value.messages.create.assert_called_once()


@patch('utils.storage.Client')
def test_write_log_to_storage_success(mock_storage_client):
    """
    Test write_log_to_storage when log is written successfully.
    """

    # Arrange
    mock_bucket = mock_storage_client.return_value.bucket.return_value
    mock_blob = mock_bucket.blob.return_value
    mock_blob.upload_from_string.return_value = None
    log_data = {'test': 'data'}

    # Act
    result = write_log_to_storage(log_data)

    # Assert
    assert result is None  # Function doesn't return anything on success
    mock_storage_client.return_value.bucket.assert_called_once_with('practice-dev-bucket')
    mock_bucket.blob.assert_called()
    mock_blob.upload_from_string.assert_called_once()


@patch('utils.storage.Client')
def test_write_log_to_storage_exception(mock_storage_client):
    """
    Test write_log_to_storage when an exception occurs.
    """

    # Arrange
    mock_bucket = mock_storage_client.return_value.bucket.return_value
    mock_bucket.blob.side_effect = Exception('Storage error')
    log_data = {'test': 'data'}

    # Act
    result = write_log_to_storage(log_data)

    # Assert
    assert result is None  # Function returns None on exception
    mock_storage_client.return_value.bucket.assert_called_once()


@patch('utils.secretmanager.SecretManagerServiceClient')
def test_access_secret_success(mock_secret_client):
    """
    Test access_secret when secret is retrieved successfully.
    """

    # Arrange
    mock_response = MagicMock()
    mock_response.payload.data.decode.return_value = 'secret_value'
    mock_secret_client.return_value.access_secret_version.return_value = mock_response

    # Act
    secret = access_secret('TEST_SECRET')

    # Assert
    assert secret == 'secret_value'
    mock_secret_client.return_value.access_secret_version.assert_called_once()


@patch('utils.secretmanager.SecretManagerServiceClient')
def test_access_secret_exception(mock_secret_client):
    """
    Test access_secret when an exception occurs.
    """

    # Arrange
    mock_secret_client.return_value.access_secret_version.side_effect = Exception('Secret Manager error')

    # Act
    secret = access_secret('TEST_SECRET')

    # Assert
    assert secret is None
    mock_secret_client.return_value.access_secret_version.assert_called_once()
