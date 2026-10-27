import logging

from celery import shared_task

from crypto import services

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def fetch_snapshot_task(self, source_name=None):
    """Celery-задача сбора снимка цен. Вся бизнес-логика — в services.collect_snapshot;
    здесь пока только обёртка: логируем запуск и вызываем сервис.

    bind=True даёт доступ к self (инстансу задачи) — он понадобится на этапе
    с retry (self.retry(...), self.request.retries и т.д.).
    """
    logger.info("[task=%s] запуск сбора снимка, source=%s", self.request.id, source_name)
    return services.collect_snapshot(source_name)
