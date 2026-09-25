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


def make_snapshot_with_changes(changes):
    """changes — изменения за 24ч по монетам; None означает «данных нет»."""
    snapshot = Snapshot.objects.create(source="coingecko")
    CoinPrice.objects.bulk_create(
        CoinPrice(
            snapshot=snapshot,
            name=f"Coin {number}",
            symbol=f"C{number}",
            price=1,
            price_change_24h=change,
            market_cap=1,
            total_volume=1,
        )
        for number, change in enumerate(changes)
    )
    return snapshot


def test_top_movers_sorted_by_change_descending():
    make_snapshot_with_changes([1, 50, 10])

    response = APIClient().get(reverse("top-movers"))

    assert [coin["price_change_24h"] for coin in response.data] == [50, 10, 1]


def test_top_movers_excludes_coins_without_change():
    """NULL в Postgres больше любого числа — без фильтра такие монеты возглавили бы топ."""
    make_snapshot_with_changes([5, None, 10, None])

    response = APIClient().get(reverse("top-movers"))

    assert [coin["price_change_24h"] for coin in response.data] == [10, 5]


def test_top_movers_returns_at_most_ten():
    make_snapshot_with_changes(list(range(15)))

    response = APIClient().get(reverse("top-movers"))

    assert len(response.data) == 10


def test_top_movers_uses_only_latest_snapshot():
    make_snapshot_with_changes([99])
    make_snapshot_with_changes([1, 2])

    response = APIClient().get(reverse("top-movers"))

    assert [coin["price_change_24h"] for coin in response.data] == [2, 1]


def test_top_movers_on_empty_database_returns_empty_list():
    response = APIClient().get(reverse("top-movers"))

    assert response.status_code == 200
    assert response.data == []


def test_top_movers_uses_single_query(django_assert_num_queries):
    make_snapshot_with_changes([1, 2, 3])

    with django_assert_num_queries(1):
        response = APIClient().get(reverse("top-movers"))

    assert response.status_code == 200