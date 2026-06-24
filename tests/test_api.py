import requests
from src.crypto import APIClient

def test_api_success(mocker):
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"data":"ok"}
    mock_response.raise_for_status.return_value = None

    mock_get = mocker.patch("requests.get", return_value=mock_response)

    client = APIClient()

    result = client.get_data("http://fake-url")
    assert result == {"data":"ok"}
    mock_get.assert_called_once()


def test_api_retry_success(mocker):
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"data":"ok"}
    mock_response.raise_for_status.return_value = None
    mock_get = mocker.patch("requests.get", side_effect=[requests.RequestException("fail"), mock_response])
    client = APIClient()
    result = client.get_data("http://fake-url")
    assert result == {"data":"ok"}
    assert mock_get.call_count == 2