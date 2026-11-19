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
