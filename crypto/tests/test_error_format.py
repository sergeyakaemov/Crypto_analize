import pytest
from rest_framework.test import APIClient

from crypto.tests.helpers import api_reverse

pytestmark = pytest.mark.django_db


def test_unhandled_error_returns_500_in_common_format(mocker):
    mocker.patch("crypto.services.market_stats", side_effect=RuntimeError("boom"))

    response = APIClient().get(api_reverse("market-stats"))

    assert response.status_code == 500
    assert response.json() == {
        "error": "Внутренняя ошибка сервера.",
        "code": "server_error",
    }


def test_not_authenticated_returns_401_in_common_format():
    response = APIClient().get(api_reverse("watchlist-list"))

    assert response.status_code == 401
    assert response.json()["code"] == "not_authenticated"
    assert set(response.json()) == {"error", "code"}


def test_missing_watchlist_item_returns_404_in_common_format(admin_api_client):

    response = admin_api_client.delete(api_reverse("watchlist-detail", pk=666))

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"
    assert set(response.json()) == {"error", "code"}


def test_unknown_api_path_returns_404_in_common_format():
    response = APIClient().get("/api/v1/nope/")

    assert response.status_code == 404
    assert response.json() == {"error": "Не найдено.", "code": "not_found"}


def test_unknown_non_api_path_keeps_html_404(client):
    response = client.get("/nope/")

    assert response.status_code == 404
    assert response["Content-Type"].startswith("text/html")
