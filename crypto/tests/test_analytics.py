import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from crypto.models import Snapshot

pytestmark = pytest.mark.django_db


# В тестах market-stats капитализацию делаем равной цене —
# тогда ожидаемые суммы считаются в уме.


def test_market_stats_returns_expected_structure(make_snapshot):
    make_snapshot(price=[1, 2, 3], market_cap=[1, 2, 3])

    response = APIClient().get(reverse("market-stats"))

    assert response.status_code == 200
    assert set(response.data) == {
        "min_price",
        "max_price",
        "avg_price",
        "total_market_cap",
    }


def test_market_stats_counts_only_latest_snapshot(make_snapshot):
    make_snapshot(price=[100, 200], market_cap=[100, 200])
    make_snapshot(price=[1, 2, 3], market_cap=[1, 2, 3])

    response = APIClient().get(reverse("market-stats"))

    assert response.data["min_price"] == "1.000000000000"
    assert response.data["max_price"] == "3.000000000000"
    assert response.data["avg_price"] == "2.000000000000"
    assert response.data["total_market_cap"] == "6.00"


def test_market_stats_on_empty_database_returns_nulls():
    response = APIClient().get(reverse("market-stats"))

    assert response.status_code == 200
    assert response.data == {
        "min_price": None,
        "max_price": None,
        "avg_price": None,
        "total_market_cap": None,
    }


def test_market_stats_with_empty_latest_snapshot_returns_nulls(make_snapshot):
    make_snapshot(price=[1, 2, 3], market_cap=[1, 2, 3])
    make_snapshot()

    response = APIClient().get(reverse("market-stats"))

    assert response.data["max_price"] is None


def test_market_stats_uses_single_query(make_snapshot, django_assert_num_queries):
    make_snapshot(price=[1, 2, 3], market_cap=[1, 2, 3])

    with django_assert_num_queries(1):
        response = APIClient().get(reverse("market-stats"))

    assert response.status_code == 200


def test_top_movers_sorted_by_change_descending(make_snapshot):
    make_snapshot(price_change_24h=[1, 50, 10])

    response = APIClient().get(reverse("top-movers"))

    assert [coin["price_change_24h"] for coin in response.data] == [50, 10, 1]


def test_top_movers_excludes_coins_without_change(make_snapshot):
    """NULL в Postgres больше любого числа — без фильтра такие монеты возглавили бы топ."""
    make_snapshot(price_change_24h=[5, None, 10, None])

    response = APIClient().get(reverse("top-movers"))

    assert [coin["price_change_24h"] for coin in response.data] == [10, 5]


def test_top_movers_returns_at_most_ten(make_snapshot):
    make_snapshot(price_change_24h=list(range(15)))

    response = APIClient().get(reverse("top-movers"))

    assert len(response.data) == 10


def test_top_movers_uses_only_latest_snapshot(make_snapshot):
    make_snapshot(price_change_24h=[99])
    make_snapshot(price_change_24h=[1, 2])

    response = APIClient().get(reverse("top-movers"))

    assert [coin["price_change_24h"] for coin in response.data] == [2, 1]


def test_top_movers_on_empty_database_returns_empty_list():
    response = APIClient().get(reverse("top-movers"))

    assert response.status_code == 200
    assert response.data == []


def test_top_movers_with_empty_latest_snapshot_returns_empty_list(make_snapshot):
    make_snapshot(price_change_24h=[1, 2])
    make_snapshot()

    response = APIClient().get(reverse("top-movers"))

    assert response.status_code == 200
    assert response.data == []


def test_top_movers_uses_single_query(make_snapshot, django_assert_num_queries):
    make_snapshot(price_change_24h=[1, 2, 3])

    with django_assert_num_queries(1):
        response = APIClient().get(reverse("top-movers"))

    assert response.status_code == 200


def test_volume_leaders_sorted_by_volume_descending(make_snapshot):
    make_snapshot(total_volume=[10, 300, 50])

    response = APIClient().get(reverse("volume-leaders"))

    assert [coin["total_volume"] for coin in response.data] == ["300.00", "50.00", "10.00"]


def test_volume_leaders_returns_at_most_ten(make_snapshot):
    make_snapshot(total_volume=list(range(1, 16)))

    response = APIClient().get(reverse("volume-leaders"))

    assert len(response.data) == 10


def test_volume_leaders_uses_only_latest_snapshot(make_snapshot):
    make_snapshot(total_volume=[999])
    make_snapshot(total_volume=[10, 20])

    response = APIClient().get(reverse("volume-leaders"))

    assert [coin["total_volume"] for coin in response.data] == ["20.00", "10.00"]


def test_volume_leaders_breaks_created_at_tie_by_id(make_snapshot):
    make_snapshot(total_volume=[999])
    make_snapshot(total_volume=[10])
    Snapshot.objects.update(created_at=timezone.now())

    response = APIClient().get(reverse("volume-leaders"))

    assert [coin["total_volume"] for coin in response.data] == ["10.00"]


def test_volume_leaders_on_empty_database_returns_empty_list():
    response = APIClient().get(reverse("volume-leaders"))

    assert response.status_code == 200
    assert response.data == []


def test_volume_leaders_with_empty_latest_snapshot_returns_empty_list(make_snapshot):
    make_snapshot(total_volume=[10, 20])
    make_snapshot()

    response = APIClient().get(reverse("volume-leaders"))

    assert response.status_code == 200
    assert response.data == []


def test_volume_leaders_uses_single_query(make_snapshot, django_assert_num_queries):
    make_snapshot(total_volume=[1, 2, 3])

    with django_assert_num_queries(1):
        response = APIClient().get(reverse("volume-leaders"))

    assert response.status_code == 200
