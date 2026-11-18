import pytest
from rest_framework.test import APIClient

from crypto.throttling import AdminRateThrottle, NonAdminUserRateThrottle

pytestmark = pytest.mark.django_db

SNAPSHOTS_URL = "/api/v1/snapshots/"


def test_anonymous_gets_429_after_five_requests():
    """Аноним: 5 запросов в минуту проходят, шестой отбивается с Retry-After."""
    client = APIClient()

    for _ in range(5):
        assert client.get(SNAPSHOTS_URL).status_code == 200

    response = client.get(SNAPSHOTS_URL)

    assert response.status_code == 429
    assert response.has_header("Retry-After")


def test_authenticated_user_is_not_limited_by_anon_rate(user_api_client):
    """Залогиненного не ограничивает лимит анонима: 6 запросов подряд — без 429."""

    for _ in range(6):
        assert user_api_client.get(SNAPSHOTS_URL).status_code == 200


def test_admin_throttle_counts_only_superusers(mocker, admin_user, user):
    """Суперпользователь получает ключ (считается), обычный пользователь — None."""
    throttle = AdminRateThrottle()

    superuser_request = mocker.Mock(user=admin_user)
    regular_request = mocker.Mock(user=user)

    assert (
        throttle.get_cache_key(superuser_request, view=None)
        == f"throttle_admin_{admin_user.pk}"
    )
    assert throttle.get_cache_key(regular_request, view=None) is None


def test_non_admin_throttle_skips_superuser(mocker, admin_user, user):
    """Суперпользователь получает None, обычный пользователь — ключ."""
    throttle = NonAdminUserRateThrottle()

    superuser_request = mocker.Mock(user=admin_user)
    regular_request = mocker.Mock(user=user)

    assert throttle.get_cache_key(superuser_request, view=None) is None
    assert (
        throttle.get_cache_key(regular_request, view=None) == f"throttle_user_{user.pk}"
    )
