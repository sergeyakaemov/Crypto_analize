import logging

import requests
from celery import shared_task

from crypto import services
from crypto.retry import TOO_MANY_REQUESTS

logger = logging.getLogger(__name__)

# Сетевые ошибки — то, что имеет смысл повторить: соединение не установилось,
# сервер не ответил вовремя или связь оборвалась посреди ответа. HTTPError сюда
# не входит: его нужно различать по коду статуса внутри задачи.
NETWORK_ERRORS = (
    requests.ConnectionError,
    requests.Timeout,
    requests.exceptions.ChunkedEncodingError,
)


class TemporaryExchangeError(Exception):
    """Биржа ответила 5xx, 429. Отдельный тип нужен, чтобы отправить эту ошибку через
    autoretry_for: retry_backoff и retry_jitter действуют только там, а ручной
    self.retry() без countdown ждёт фиксированные default_retry_delay (180 с)."""


def _is_retryable_http_error(error: requests.HTTPError) -> bool:
    """4xx — клиентская ошибка (неверные параметры, не найдено и т.п.):
    повторный одинаковый запрос даст тот же результат, ретраить бессмысленно.
    Но 429 - исключение. У Coingecko это значит "Лимит исчерпан, приходи позже".
    5xx — проблема на стороне сервера биржи, обычно временная: есть смысл
    попробовать ещё раз."""
    status_code = error.response.status_code if error.response is not None else None
    return status_code is not None and (
        status_code >= 500 or status_code == TOO_MANY_REQUESTS
    )


@shared_task(
    bind=True,
    autoretry_for=(*NETWORK_ERRORS, TemporaryExchangeError),
    max_retries=5,
    retry_backoff=True,  # экспоненциальный backoff: 1с, 2с, 4с, 8с, 16с...
    retry_backoff_max=600,  # не ждать дольше 10 минут между попытками
    retry_jitter=True,  # + случайный разброс, чтобы несколько ретраев
    # не били по бирже одновременно (thundering herd)
)
def fetch_snapshot_task(self, source_name=None):
    """Celery-задача сбора снимка цен.

    autoretry_for покрывает "чистые" сетевые сбои (обрыв соединения, таймаут)
    — Celery сам поймает их и перевыполнит задачу с задержкой. HTTPError
    обрабатываем вручную ниже, потому что внутри него нужно смотреть код
    статуса: 5xx, 429 превращаем в TemporaryExchangeError из autoretry_for, чтобы он
    шёл через тот же backoff, что и сетевые ошибки, а остальные 4xx — пробрасываем
    сразу, без единой попытки повтора. Ошибки, не связанные с сетью
    (IntegrityError, ImproperlyConfigured и т.п.), никак не перехватываются
    и падают как есть — это осознанно: ретраить баг в данных или в коде
    бессмысленно, задача должна сразу попасть в FAILURE.
    """
    logger.info(
        "[task=%s] запуск сбора снимка, source=%s", self.request.id, source_name
    )

    try:
        return services.collect_snapshot(source_name)
    except requests.HTTPError as error:
        if _is_retryable_http_error(error):
            logger.warning(
                "[task=%s] сервер биржи ответил %s — ретраим",
                self.request.id,
                error.response.status_code,
            )
            raise TemporaryExchangeError(
                f"биржа ответила {error.response.status_code}"
            ) from error
        logger.error(
            "[task=%s] клиентская ошибка %s — ретраить бессмысленно",
            self.request.id,
            error.response.status_code if error.response is not None else "?",
        )
        raise
