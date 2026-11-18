import pytest
from rest_framework.test import APIClient

from crypto.tests.helpers import api_reverse

pytestmark = pytest.mark.django_db


def market_caps_from(response):
    return [snapshot["total_market_cap"] for snapshot in response.data["results"]]


def test_order_by_total_market_cap_desc(make_snapshot):
    make_snapshot(market_cap=[10, 20])
    make_snapshot(market_cap=[5])
    make_snapshot()

    response = APIClient().get(
        api_reverse("snapshot-list"), {"ordering": "-total_market_cap"}
    )

    assert market_caps_from(response) == ["30.00", "5.00", "0.00"]


def test_order_by_total_market_cap_asc(make_snapshot):
    make_snapshot()
    make_snapshot(market_cap=[5])
    make_snapshot(market_cap=[10, 20])

    response = APIClient().get(
        api_reverse("snapshot-list"), {"ordering": "total_market_cap"}
    )

    assert market_caps_from(response) == ["0.00", "5.00", "30.00"]
