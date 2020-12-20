# pylint: disable=redefined-outer-name
"""Tests for export """
import json
from unittest.mock import patch
import pytest
from falcon import testing
from service.transforms.transform import TransformBase
from service.resources.export import Export
import service.microservice

CLIENT_HEADERS = {
    "ACCESS_KEY": "1234567"
}
CLIENT_ENV = {
    "ACCESS_KEY": CLIENT_HEADERS["ACCESS_KEY"],
    "X_APIKEY": "abcdefg",
    "API_BASE_URL": "https://localhost",
    "SENDGRID_API_KEY": "abc",
    "EXPORT_TOKEN": "xyz",
    "SLACK_API_TOKEN": "",
    "EXPORT_EMAIL_FROM": "to@localhost",
    "EXPORT_EMAIL_TO": "to@localhost",
    "EXPORT_EMAIL_CC": "cc@localhost",
    "EXPORT_EMAIL_BCC": "bcc@localhost"
}

@pytest.fixture()
def client():
    """ client fixture """
    return testing.TestClient(app=service.microservice.start_service())

@pytest.fixture
def mock_env(monkeypatch):
    """ mock environment access key """
    for key in CLIENT_ENV:
        monkeypatch.setenv(key, CLIENT_ENV[key])

def test_export(client, mock_env):
    # pylint: disable=unused-argument
    # mock_env is a fixture and creates a false positive for pylint
    """Test export message response"""

    with open('tests/mocks/export_submissions.json', 'r') as file_obj:
        mock_responses = json.load(file_obj)

    assert mock_responses

    with patch('service.modules.permit_applications.requests.get') as mock:
        mock.return_value.status_code = 200
        mock.return_value.json.return_value = mock_responses

        with patch('service.resources.export.Export.send_email') as mock_send_email:
            mock_send_email.return_value.status_code = 202
            mock_send_email.return_value.body = "Content"
            mock_send_email.return_value.headers = "X-Message-Id: 12345"

            response = client.simulate_get(
                '/export', params={
                    "actionState": "Export to PTS",
                    "token": "xyz",
                    "start_date": "2020-01-01",
                    "name": "Building Permit Application",
                    "send_email": "1"})

            assert response.status_code == 200

            response_json = response.json
            assert response_json['status'] == 'success'

            assert 'data' in response_json
            assert 'responses' in response_json['data']

        with patch('service.resources.export.Export.sftp') as mock_sftp:
            mock_sftp.return_value.status_code = 200
            mock_sftp.return_value.body = "Data"

            response = client.simulate_get(
                '/export', params={
                    "actionState": "Export to PTS",
                    "token": "xyz",
                    "form_id": "123",
                    "start_date": "2020-01-01",
                    "name": "Building Permit Application",
                    "sftp_upload": "1"})

            assert response.status_code == 200

            response_json = response.json
            assert response_json['status'] == 'success'

            assert 'data' in response_json
            assert 'responses' in response_json['data']

def test_export_exception(client, mock_env):
    # pylint: disable=unused-argument
    # mock_env is a fixture and creates a false positive for pylint
    """Test export exception """

    with patch('service.modules.permit_applications.requests.get') as mock:
        mock.return_value.status_code = 500
        mock.side_effect = ValueError('ERROR_TEST')

        response = client.simulate_get(
            '/export', params={
                "actionState": "Export to PTS",
                "token": "xyz",
                "send_email": "1"})

        assert response.status_code == 500

        response_json = response.json
        assert response_json['status'] == 'error'

def test_export_exception_access(client, mock_env):
    # pylint: disable=unused-argument
    # mock_env is a fixture and creates a false positive for pylint
    """Test export exception access """

    response = client.simulate_get(
        '/export', params={
            "actionState": "Export to PTS",
            "token": "fail_me",
            "send_email": "1"})

    response_json = response.json
    assert response_json['status'] == 'error'
    assert response_json['message'] == 'Unauthorized'

def test_export_exception_email(client, mock_env):
    # pylint: disable=unused-argument
    # mock_env is a fixture and creates a false positive for pylint
    """Test export email exception """

    with open('tests/mocks/export_submissions.json', 'r') as file_obj:
        mock_responses = json.load(file_obj)

    assert mock_responses

    with patch('service.modules.permit_applications.requests.get') as mock:
        mock.return_value.status_code = 200
        mock.return_value.json.return_value = mock_responses

        response = client.simulate_get(
            '/export', params={
                "actionState": "Export to PTS",
                "token": "xyz",
                "send_email": "1"})

        assert response.status_code == 500

        response_json = response.json
        assert response_json['status'] == 'error'

def test_transform_base():
    """ Test TransformBase transform method """
    data = "test"
    assert TransformBase().transform(data, ',') == data

def test_export_exception_sftp(client, mock_env):
    # pylint: disable=unused-argument
    # mock_env is a fixture and creates a false positive for pylint
    """Test export sftp exception """

    with open('tests/mocks/export_submissions.json', 'r') as file_obj:
        mock_responses = json.load(file_obj)

    assert mock_responses

    with patch('service.modules.permit_applications.requests.get') as mock:
        mock.return_value.status_code = 200
        mock.return_value.json.return_value = mock_responses

        response = client.simulate_get(
            '/export', params={
                "actionState": "Export to PTS",
                "token": "xyz",
                "send_email": "1"})

        assert response.status_code == 500

        response_json = response.json
        assert response_json['status'] == 'error'

def test_sftp():
    """ test sftp, not a full test, full test would need to mock a FTP server
    just to make sure the function call works
    """
    response = Export().sftp('some test data', 'testfile')

    assert response.status_code == 401
