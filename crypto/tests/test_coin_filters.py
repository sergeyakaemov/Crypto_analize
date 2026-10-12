import pytest
from django.urls import reverse
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def prices_from(response):
    return sorted(float(coin["price"]) for coin in response.data["results"])


def test_filter_by_min_price(make_snapshot):
    make_snapshot(price=[10, 100, 1000])

    response = APIClient().get(reverse("coinprice-list"), {"min_price": 100})

    assert prices_from(response) == [100, 1000]


def test_filter_by_max_price(make_snapshot):
    make_snapshot(price=[10, 100, 1000])

    response = APIClient().get(reverse("coinprice-list"), {"max_price": 100})

    assert prices_from(response) == [10, 100]


def test_filter_by_price_range(make_snapshot):
    make_snapshot(price=[10, 100, 1000])

    response = APIClient().get(
        reverse("coinprice-list"), {"min_price": 50, "max_price": 500}
    )

    assert prices_from(response) == [100]


def test_zero_max_price_is_applied(make_snapshot):
    """0 ложен в Python: при проверке `if max_price` фильтр молча исчез бы."""
    make_snapshot(price=[0, 10])

    response = APIClient().get(reverse("coinprice-list"), {"max_price": 0})

    assert prices_from(response) == [0]


def test_symbol_filter_is_case_insensitive(make_snapshot):
    make_snapshot(price=[10, 100], symbol=["BTC", "ETH"])

    response = APIClient().get(reverse("coinprice-list"), {"symbol": "btc"})

    assert prices_from(response) == [10]


def test_invalid_min_price_returns_400(make_snapshot):
    make_snapshot(price=[10])

    response = APIClient().get(reverse("coinprice-list"), {"min_price": "abc"})

    assert response.status_code == 400
    assert "min_price" in response.data


def test_min_price_greater_than_max_returns_400(make_snapshot):
    make_snapshot(price=[10])

    response = APIClient().get(
        reverse("coinprice-list"), {"min_price": 100, "max_price": 50}
    )

    assert response.status_code == 400