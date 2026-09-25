import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from crypto.models import CoinPrice, Snapshot

pytestmark = pytest.mark.django_db


def make_snapshot(prices):
    """Капитализацию делаем равной цене — тогда ожидаемые суммы считаются в уме."""
    snapshot = Snapshot.objects.create(source="coingecko")
    CoinPrice.objects.bulk_create(
        CoinPrice(
            snapshot=snapshot,
            name=f"Coin {price}",
            symbol=f"C{price}",
            price=price,
            market_cap=price,
            total_volume=1,
        )
        for price in prices
    )
    return snapshot


def test_market_stats_returns_expected_structure():
    make_snapshot([1, 2, 3])

    response = APIClient().get(reverse("market-stats"))

    assert response.status_code == 200
    assert set(response.data) == {
        "min_price",
        "max_price",
        "avg_price",
        "total_market_cap",
    }


def test_market_stats_counts_only_latest_snapshot():
    make_snapshot([100, 200])
    make_snapshot([1, 2, 3])

    response = APIClient().get(reverse("market-stats"))

    assert response.data["min_price"] == 1
    assert response.data["max_price"] == 3
    assert response.data["avg_price"] == 2
    assert response.data["total_market_cap"] == 6


def test_market_stats_on_empty_database_returns_nulls():
    response = APIClient().get(reverse("market-stats"))

    assert response.status_code == 200
    assert response.data == {
        "min_price": None,
        "max_price": None,
        "avg_price": None,
        "total_market_cap": None,
    }


def test_market_stats_with_empty_latest_snapshot_returns_nulls():
    make_snapshot([1, 2, 3])
    Snapshot.objects.create(source="coingecko")

    response = APIClient().get(reverse("market-stats"))

    assert response.data["max_price"] is None


def test_market_stats_uses_single_query(django_assert_num_queries):
    make_snapshot([1, 2, 3])

    with django_assert_num_queries(1):
        response = APIClient().get(reverse("market-stats"))

    assert response.status_code == 200