import pytest
import requests
from django.core.exceptions import ImproperlyConfigured

from crypto import sources
from crypto.client import get_json


@pytest.fixture(autouse=True)
def no_sleep(mocker):
    mocker.patch("crypto.retry.time.sleep")


def test_coingecko_timeout_becomes_provider_error(mocker):
    mocker.patch("crypto.sources.get_json", side_effect=requests.Timeout("таймаут"))

    with pytest.raises(sources.ProviderError):
        sources.CoinGecko().symbol_exists("BTC")


def test_coinmarketcap_timeout_becomes_provider_error(mocker):
    mocker.patch("crypto.sources.get_json", side_effect=requests.Timeout("таймаут"))

    with pytest.raises(sources.ProviderError):
        sources.CoinMarketCap().symbol_exists("BTC")


def test_coinmarketcap_unknown_symbol_returns_false(mocker):
    response = requests.Response()
    response.status_code = 400
    mocker.patch(
        "crypto.sources.get_json",
        side_effect=requests.HTTPError(response=response),
    )

    assert sources.CoinMarketCap().symbol_exists("ZZZ") is False


def test_get_json_raises_on_http_error(mocker):
    response = requests.Response()
    response.status_code = 500
    mocker.patch("crypto.client.requests.get", return_value=response)

    with pytest.raises(requests.HTTPError):
        get_json("https://example.test")


def test_get_provider_rejects_unknown_name():
    with pytest.raises(ImproperlyConfigured):
        sources.get_provider("нет такой биржи")