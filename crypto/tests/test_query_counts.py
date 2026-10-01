import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from crypto.models import Snapshot

pytestmark = pytest.mark.django_db


def test_coin_list_query_count_does_not_grow(make_snapshot, django_assert_num_queries):
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


def test_snapshot_list_query_count_does_not_grow(make_snapshot, django_assert_num_queries):
    """Число запросов не зависит от числа снимков — иначе вернулся N+1."""
    client = APIClient()
    url = reverse("snapshot-list")

    make_snapshot(coins=3)
    with django_assert_num_queries(2):
        response = client.get(url)
    assert response.status_code == 200

    for _ in range(5):
        make_snapshot(coins=2)
    with django_assert_num_queries(2):
        response = client.get(url)
    assert response.status_code == 200


def test_snapshot_list_keeps_newest_first(make_snapshot):
    """annotate сбрасывает Meta.ordering — сортировка должна быть задана явно."""
    older = make_snapshot(coins=0)
    newer = make_snapshot(coins=0)

    response = APIClient().get(reverse("snapshot-list"))

    assert [row["id"] for row in response.data["results"]] == [newer.pk, older.pk]


def test_snapshot_model_ordering_is_deterministic():
    """При совпавшем created_at порядок задаёт вторичный ключ по id."""
    older = Snapshot.objects.create(source="coingecko")
    newer = Snapshot.objects.create(source="coingecko")
    Snapshot.objects.filter(pk__in=[older.pk, newer.pk]).update(created_at=older.created_at)

    assert list(Snapshot.objects.all()) == [newer, older]
