import pytest
import requests
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from crypto.models import WatchlistItem

pytestmark = pytest.mark.django_db

PASSWORD = "pass12345"


def list_url():
    return reverse("watchlist-list")


def detail_url(pk):
    return reverse("watchlist-detail", args=[pk])


def login(client, username):
    response = client.post(
        reverse("token_obtain_pair"),
        {"username": username, "password": PASSWORD},
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return client


@pytest.fixture
def anon_client():
    return APIClient()


@pytest.fixture
def alice_client(user):
    return login(APIClient(), user.username)


@pytest.fixture
def bob_client(other_user):
    return login(APIClient(), other_user.username)


def test_token_obtain_returns_pair(anon_client, user):
    response = anon_client.post(
        reverse("token_obtain_pair"),
        {"username": user.username, "password": PASSWORD},
    )

    assert response.status_code == status.HTTP_200_OK
    assert {"access", "refresh"} <= set(response.data)


def test_token_obtain_wrong_password_returns_401(anon_client, user):
    response = anon_client.post(
        reverse("token_obtain_pair"),
        {"username": user.username, "password": "wrong"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_token_refresh_returns_new_access(anon_client, user):
    tokens = anon_client.post(
        reverse("token_obtain_pair"),
        {"username": user.username, "password": PASSWORD},
    ).data

    response = anon_client.post(reverse("token_refresh"), {"refresh": tokens["refresh"]})

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data


def test_watchlist_requires_auth(anon_client):
    response = anon_client.get(list_url())

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers["WWW-Authenticate"].startswith("Bearer")


def test_watchlist_rejects_invalid_token(anon_client):
    anon_client.credentials(HTTP_AUTHORIZATION="Bearer not-a-real-token")

    response = anon_client.get(list_url())

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_add_returns_201_with_normalized_symbol(alice_client, provider):
    response = alice_client.post(list_url(), {"symbol": " btc "})

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["symbol"] == "BTC"
    assert set(response.data) == {"id", "symbol", "created_at"}


def test_add_ignores_user_from_body(alice_client, user, other_user, provider):
    response = alice_client.post(list_url(), {"symbol": "BTC", "user": other_user.pk})

    item = WatchlistItem.objects.get(pk=response.data["id"])
    assert item.user == user


def test_add_blank_symbol_returns_400_without_exchange_call(alice_client, provider):
    response = alice_client.post(list_url(), {"symbol": ""})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "symbol" in response.data
    provider.symbol_exists.assert_not_called()


def test_add_unknown_symbol_returns_400(alice_client, provider):
    provider.symbol_exists.return_value = False

    response = alice_client.post(list_url(), {"symbol": "zzz"})

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_add_duplicate_returns_409(alice_client, provider):
    alice_client.post(list_url(), {"symbol": "BTC"})

    response = alice_client.post(list_url(), {"symbol": "btc"})

    assert response.status_code == status.HTTP_409_CONFLICT


def test_add_when_exchange_down_returns_503(alice_client, provider):
    provider.symbol_exists.side_effect = requests.Timeout()

    response = alice_client.post(list_url(), {"symbol": "BTC"})

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


def test_users_see_only_own_items(alice_client, bob_client, provider):
    alice_client.post(list_url(), {"symbol": "BTC"})

    alice_list = alice_client.get(list_url())
    bob_list = bob_client.get(list_url())

    assert alice_list.data["count"] == 1
    assert alice_list.data["results"][0]["symbol"] == "BTC"
    assert bob_list.data["count"] == 0


def test_cannot_delete_foreign_item(alice_client, bob_client, provider):
    item_id = alice_client.post(list_url(), {"symbol": "BTC"}).data["id"]

    response = bob_client.delete(detail_url(item_id))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert WatchlistItem.objects.filter(pk=item_id).exists()


def test_delete_own_item_returns_204(alice_client, provider):
    item_id = alice_client.post(list_url(), {"symbol": "BTC"}).data["id"]

    response = alice_client.delete(detail_url(item_id))

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not WatchlistItem.objects.filter(pk=item_id).exists()


def test_update_is_not_allowed(alice_client, provider):
    item_id = alice_client.post(list_url(), {"symbol": "BTC"}).data["id"]

    response = alice_client.put(detail_url(item_id), {"symbol": "ETH"})

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
