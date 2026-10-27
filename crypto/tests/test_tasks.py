import pytest
import requests

from crypto import tasks
from crypto.models import Snapshot

pytestmark = pytest.mark.django_db


SAMPLE_DATA = [
    {
        "name": "Bitcoin",
        "symbol": "btc",
        "current_price": 50000,
        "price_change_percentage_24h": 1.5,
        "market_cap": 900000000,
        "total_volume": 30000000,
    },
]


def test_fetch_snapshot_task_success(mocker):
    """Успешное выполнение: задача сохраняет снимок и возвращает его данные."""
    mocker.patch("crypto.services.get_json", return_value=SAMPLE_DATA)

    result = tasks.fetch_snapshot_task.apply(args=[None])

    assert result.successful()
    payload = result.get()
    assert payload["coins_count"] == 1
    assert payload["source"] == "coingecko"
    assert Snapshot.objects.filter(pk=payload["snapshot_id"]).exists()


def test_fetch_snapshot_task_retries_on_connection_error(mocker):
    """Сетевой сбой (обрыв соединения) один раз — задача должна повторить
    попытку сама и в итоге выполниться успешно."""
    get_json = mocker.patch(
        "crypto.services.get_json",
        side_effect=[requests.ConnectionError("не удалось подключиться"), SAMPLE_DATA],
    )

    # .apply() выполняет задачу синхронно, в т.ч. честно проигрывая retry —
    # в отличие от прямого вызова функции, здесь self.retry() реально
    # перезапускает run(), а не просто падает.
    result = tasks.fetch_snapshot_task.apply(args=[None])

    assert result.successful()
    assert get_json.call_count == 2, "ожидали первую неудачную попытку и один ретрай"


def test_fetch_snapshot_task_does_not_retry_on_client_error(mocker):
    """HTTP 400 — ошибка в запросе, повторять его бессмысленно: задача должна
    упасть сразу, с первой же попытки, без единого ретрая."""
    response = requests.Response()
    response.status_code = 400
    get_json = mocker.patch(
        "crypto.services.get_json",
        side_effect=requests.HTTPError(response=response),
    )

    result = tasks.fetch_snapshot_task.apply(args=[None])

    assert result.failed()
    assert get_json.call_count == 1, "4xx не должен приводить к ретраю"
    assert not Snapshot.objects.exists()
