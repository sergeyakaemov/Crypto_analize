import logging

import requests
from celery import shared_task

from crypto import services

logger = logging.getLogger(__name__)

# Сетевые ошибки — то, что имеет смысл повторить: соединение не установилось,
# сервер не ответил вовремя, либо сервер сам сообщил о временной проблеме
# (5xx). Будем различать HTTPError по коду статуса отдельно внутри задачи,
# поэтому в autoretry_for его не перечисляем целиком.
NETWORK_ERRORS = (requests.ConnectionError, requests.Timeout)


def _is_retryable_http_error(error: requests.HTTPError) -> bool:
    """4xx — клиентская ошибка (неверные параметры, не найдено и т.п.):
    повторный одинаковый запрос даст тот же результат, ретраить бессмысленно.
    5xx — проблема на стороне сервера биржи, обычно временная: есть смысл
    попробовать ещё раз."""
    status_code = error.response.status_code if error.response is not None else None
    return status_code is not None and status_code >= 500


@shared_task(
    bind=True,
    autoretry_for=NETWORK_ERRORS,
    max_retries=5,
    retry_backoff=True,       # экспоненциальный backoff: 1с, 2с, 4с, 8с, 16с...
    retry_backoff_max=600,    # не ждать дольше 10 минут между попытками
    retry_jitter=True,        # + случайный разброс, чтобы несколько ретраев
                               # не били по бирже одновременно (thundering herd)
)
def fetch_snapshot_task(self, source_name=None):
    """Celery-задача сбора снимка цен.

    autoretry_for покрывает "чистые" сетевые сбои (обрыв соединения, таймаут)
    — Celery сам поймает их и перевыполнит задачу с задержкой. HTTPError
    обрабатываем вручную ниже, потому что внутри него нужно смотреть код
    статуса: 5xx ретраим так же, как сетевые ошибки, а 4xx — пробрасываем
    сразу, без единой попытки повтора. Ошибки, не связанные с сетью
    (IntegrityError, ImproperlyConfigured и т.п.), никак не перехватываются
    и падают как есть — это осознанно: ретраить баг в данных или в коде
    бессмысленно, задача должна сразу попасть в FAILURE.
    """
    logger.info("[task=%s] запуск сбора снимка, source=%s", self.request.id, source_name)

    try:
        return services.collect_snapshot(source_name)
    except requests.HTTPError as error:
        if _is_retryable_http_error(error):
            logger.warning(
                "[task=%s] сервер биржи ответил %s — ретраим",
                self.request.id, error.response.status_code,
            )
            raise self.retry(exc=error)
        logger.error(
            "[task=%s] клиентская ошибка %s — ретраить бессмысленно",
            self.request.id, error.response.status_code if error.response is not None else '?',
        )
        raise
