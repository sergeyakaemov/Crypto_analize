import pytest
import requests
from prompt_toolkit.key_binding.bindings.named_commands import backward_word
from redis import backoff

from crypto import tasks
from crypto.models import Snapshot

pytestmark = pytest.mark.django_db


def test_fetch_snapshot_task_success(mocker, exchange_response):
    """Успешное выполнение: задача сохраняет снимок и возвращает его данные."""
    mocker.patch("crypto.services.get_json", return_value=exchange_response)

    result = tasks.fetch_snapshot_task.apply(args=[None])

    assert result.successful()
    payload = result.get()
    assert payload["coins_count"] == 1
    assert payload["source"] == "coingecko"
    assert Snapshot.objects.filter(pk=payload["snapshot_id"]).exists()


@pytest.mark.parametrize(
    "error_class",
    [
        requests.ConnectionError,
        requests.Timeout,
        requests.exceptions.ChunkedEncodingError,
    ],
)
def test_fetch_snapshot_task_retries_on_network_error(mocker, exchange_response, error_class):
    """Сетевой сбой один раз — задача должна повторить попытку сама и в итоге
    выполниться успешно."""
    get_json = mocker.patch(
        "crypto.services.get_json",
        side_effect=[error_class("сетевой сбой"), exchange_response],
    )

    # .apply() выполняет задачу синхронно, в т.ч. честно проигрывая retry —
    # в отличие от прямого вызова функции, здесь self.retry() реально
    # перезапускает run(), а не просто падает.
    result = tasks.fetch_snapshot_task.apply(args=[None])

    assert result.successful()
    assert get_json.call_count == 2, "ожидали первую неудачную попытку и один ретрай"


def test_fetch_snapshot_task_gives_up_after_max_retries(mocker):
    """Сеть не восстановилась — задача не повторяет запрос бесконечно."""
    get_json = mocker.patch(
        "crypto.services.get_json",
        side_effect=requests.ConnectionError("сетевой сбой"),
    )

    result = tasks.fetch_snapshot_task.apply(args=[None])

    assert result.failed()
    assert get_json.call_count == 6, "ожидали первую попытку и 5 ретраев"


@pytest.mark.parametrize("status_code", [503, 429])
def test_fetch_snapshot_task_retries_on_temporary_http_error_with_backoff(mocker, exchange_response, status_code):
    """HTTP 503, 429 — временная проблема биржи: задача повторяет запрос с
    экспоненциальной задержкой и в итоге выполняется успешно."""
    response = requests.Response()
    response.status_code = status_code
    error = requests.HTTPError(response=response)
    get_json = mocker.patch(
        "crypto.services.get_json",
        side_effect=[error, error, exchange_response],
    )
    retry = mocker.spy(tasks.fetch_snapshot_task, "retry")

    result = tasks.fetch_snapshot_task.apply(args=[None])

    assert result.successful()
    assert get_json.call_count == 3, "ожидали две неудачные попытки и успешную третью"
    countdowns = [call.kwargs["countdown"] for call in retry.call_args_list]
    assert countdowns[0] <= 1 and countdowns[1] <= 2, "задержка должна расти экспоненциально"


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
