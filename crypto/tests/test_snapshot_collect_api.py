import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.fixture
def eager_celery(monkeypatch):
    """Выполняет задачи синхронно внутри тестового процесса, без реального
    воркера и брокера.

    Каждый флаг меняем там, где его реально читает Celery:
    - task_always_eager читается из app.conf при каждом .delay();
    - store_eager_result Celery один раз копирует из конфига в атрибут
      задачи при её привязке к приложению, поэтому app.conf тут уже
      не поможет — патчим саму задачу.
    Без store_eager_result eager-результат не попадёт в result backend,
    и TaskStatusView ничего не найдёт по task_id.
    monkeypatch сам вернёт оба значения после теста."""
    from config.celery import app
    from crypto.tasks import fetch_snapshot_task

    monkeypatch.setattr(app.conf, 'task_always_eager', True)
    monkeypatch.setattr(app.conf, 'task_store_eager_result', True)
    monkeypatch.setattr(fetch_snapshot_task, 'store_eager_result', True)


@pytest.fixture
def mock_delay(mocker):
    """Подменяет постановку задачи в очередь: брокер и Redis не нужны."""
    delay = mocker.patch("crypto.views.fetch_snapshot_task.delay")
    delay.return_value = mocker.Mock(id="task-id", status="PENDING")
    return delay


def test_collect_returns_202_with_task_id(eager_celery, mocker, exchange_response):
    mocker.patch("crypto.services.get_json", return_value=exchange_response)

    response = APIClient().post('/api/snapshots/collect/')

    assert response.status_code == 202
    assert 'task_id' in response.data


@pytest.mark.parametrize(
    "body",
    [
        {"source": "нет такой биржи"},
        {"source": ["coingecko"]},
        {"source": {}},
        {"source": None},
        [1, 2],
    ],
)
def test_collect_rejects_invalid_body(mock_delay, body):
    """Неверный запрос отбивается сразу: 400 и никакой задачи в очереди."""
    response = APIClient().post('/api/snapshots/collect/', body, format='json')

    assert response.status_code == 400
    mock_delay.assert_not_called()


def test_collect_passes_source_to_task(mock_delay):
    response = APIClient().post(
        '/api/snapshots/collect/', {'source': 'coinmarketcap'}, format='json'
    )

    assert response.status_code == 202
    mock_delay.assert_called_once_with('coinmarketcap')


def test_task_status_reports_success_and_result(eager_celery, mocker, exchange_response):
    mocker.patch("crypto.services.get_json", return_value=exchange_response)

    collect_response = APIClient().post('/api/snapshots/collect/')
    task_id = collect_response.data['task_id']

    status_response = APIClient().get(f'/api/tasks/{task_id}/')

    assert status_response.status_code == 200
    assert status_response.data['status'] == 'SUCCESS'
    assert status_response.data['result']['coins_count'] == 1


def test_task_status_for_unknown_id_is_pending():
    """Несуществующий task_id — Celery не считает это ошибкой, просто говорит
    PENDING (не умеет отличить "ещё не начался" от "такого никогда не было")."""
    response = APIClient().get('/api/tasks/00000000-0000-0000-0000-000000000000/')

    assert response.status_code == 200
    assert response.data['status'] == 'PENDING'
