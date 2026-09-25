import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from crypto.models import CoinPrice, Snapshot

pytestmark = pytest.mark.django_db


def make_snapshot(coins):
    snapshot = Snapshot.objects.create(source="coingecko")
    CoinPrice.objects.bulk_create(
        CoinPrice(
            snapshot=snapshot,
            name=f"Coin {number}",
            symbol=f"C{number}",
            price=1,
            market_cap=1,
            total_volume=1,
        )
        for number in range(coins)
    )
    return snapshot


def test_coin_list_query_count_does_not_grow(django_assert_num_queries):
    """Число запросов не зависит от числа монет — иначе вернулся N+1."""
    client = APIClient()
    url = reverse("coinprice-list")

    make_snapshot(coins=3)
    with django_assert_num_queries(2):
        response = client.get(url)
    assert response.status_code == 200

    make_snapshot(coins=10)
    with django_assert_num_queries(2):
        response = client.get(url)
    assert response.status_code == 200