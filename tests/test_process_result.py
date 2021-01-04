# pylint: disable=redefined-outer-name
"""Tests for export """
import json
from unittest.mock import patch
import unittest.mock as mock
import pytest
import pysftp
from falcon import testing
from service.modules.process_result import ProcessResultFile
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
    "EXPORT_EMAIL_FROM": "",
    "EXPORT_EMAIL_TO": "to@localhost",
    "EXPORT_EMAIL_CC": "cc@localhost",
    "EXPORT_EMAIL_BCC": "bcc@localhost",
    "SUMMARY_EMAIL_TO": "to@localhost",
    "SUMMARY_EMAIL_CC": "cc@localhost",
    "SUMMARY_EMAIL_BCC": "bcc@localhost"
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

def test_process_result(client, mock_env):
    # pylint: disable=unused-argument
    # mock_env is a fixture and creates a false positive for pylint
    """Test export message response"""

    with open('tests/mocks/export_submissions.json', 'r') as file_obj:
        mock_responses = json.load(file_obj)

    assert mock_responses
    with patch('service.modules.permit_applications.requests.get') as mock:
        mock.return_value.status_code = 200
        mock.return_value.json.return_value = mock_responses

        with patch('service.modules.permit_applications.requests.patch') as mock_patch:
            mock_patch.return_value.text = "TEST"
            mock_patch.return_value.status_code = 200

            with patch('service.resources.export.Export.send_email') as mock_send_email:
                mock_send_email.return_value.status_code = 202
                mock_send_email.return_value.body = "Content"
                mock_send_email.return_value.headers = "X-Message-Id: 12345"

                with patch('service.modules.process_result.ProcessResultFile.get_result_file') as mock_result_file:
                    mock_patch.return_value.text = "PTS_Export_09_26.csv"
                    mock_patch.return_value.status_code = 200

                    response = client.simulate_get(
                        '/processResultFile', params={
                            "token": "xyz"})
                    assert response.status_code == 200

@mock.patch.object(
    target=pysftp,
    attribute='Connection',
    autospec=True,
    return_value=mock.Mock(
        spec=pysftp.Connection,
        __enter__=lambda self: self,
        __exit__=lambda *args: None
    )
)
def test_get_result_file(file_name):
    """ Test get result file """
    file_name = ProcessResultFile().get_result_file('tests/mocks/result_file.csv')
    assert file_name != ''

def test_get_result_file_exception():
    """ Test get result file """
    file_name = ProcessResultFile().get_result_file('tests/mocks/dummy.csv')
    assert file_name == ''

def test_get_exported_submissions():
    """ test get exported submissions """
    with open('tests/mocks/export_submissions.json', 'r') as file_obj:
        mock_responses = json.load(file_obj)

    assert mock_responses

    with patch('service.modules.permit_applications.requests.get') as mock:
        mock.return_value.status_code = 200
        mock.return_value.json.return_value = mock_responses

        ret = ProcessResultFile().get_exported_submissions()

        assert ret

def test_process_file(client, mock_env):
    # pylint: disable=unused-argument
    """ Test process file """
    #file_name = 'tests/mocks/result_file.csv'

    with patch('service.resources.export.Export.send_email') as mock_send_email:
        mock_send_email.return_value.status_code = 202
        mock_send_email.return_value.body = "Content"
        mock_send_email.return_value.headers = "X-Message-Id: 12345"

        with patch('service.modules.permit_applications.requests.patch') as mock_patch:
            mock_patch.return_value.text = "TEST"
            mock_patch.return_value.status_code = 200

            response = client.simulate_get(
            '/processResultFile', params={
                "token": "xyz"})

            assert response.status_code == 200

def test_process_result_exception(client, mock_env):
    # pylint: disable=unused-argument
    # mock_env is a fixture and creates a false positive for pylint
    """Test export exception """

    with patch('service.modules.permit_applications.requests.get') as mock:
        mock.return_value.status_code = 500
        mock.side_effect = ValueError('ERROR_TEST')

        response = client.simulate_get(
            '/processResultFile', params={
                "token": "xyzbb"})

        assert response.status_code == 500

        response_json = response.json
        assert response_json['status'] == 'error'

def test_process_result_exception_access(client, mock_env):
    # pylint: disable=unused-argument
    # mock_env is a fixture and creates a false positive for pylint
    """Test export exception access """

    response = client.simulate_get(
        '/processResultFile', params={
            "token": "fail_me"})

    response_json = response.json
    assert response_json['status'] == 'error'
    assert response_json['message'] == 'Unauthorized'
