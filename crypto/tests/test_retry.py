import pytest
import requests

from crypto.retry import retry


def http_error(status_code):
    """HTTPError с нужным кодом ответа — retry смотрит именно на response.status_code."""
    response = requests.Response()
    response.status_code = status_code
    return requests.HTTPError(response=response)


def test_retries_on_429():
    calls = []

    @retry(max_attempts=3, delay=0)
    def throttled():
        calls.append(1)
        raise http_error(429)

    with pytest.raises(requests.RequestException):
        throttled()

    assert len(calls) == 3


def test_does_not_retry_on_404():
    calls = []

    @retry(max_attempts=3, delay=0)
    def missing():
        calls.append(1)
        raise http_error(404)

    with pytest.raises(requests.HTTPError) as error:
        missing()

    assert error.value.response.status_code == 404
    assert len(calls) == 1