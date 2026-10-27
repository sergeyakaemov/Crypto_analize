from django.conf import settings
from django.core.management import BaseCommand

from crypto.sources import SOURCES
from crypto.tasks import fetch_snapshot_task


class Command(BaseCommand):
    help = "Ставит в очередь Celery-задачу сбора цен монет с биржи и сохранения снимка"

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            choices=SOURCES,
            default=None,
            help="Источник данных (по умолчанию EXCHANGE_PROVIDER из .env)",
        )

    def handle(self, *args, **options):
        name = options["source"] or settings.EXCHANGE_PROVIDER

        # .delay() — короткая форма apply_async(): кладёт сообщение в очередь
        # и сразу возвращает управление, не дожидаясь выполнения. Реальную
        # работу сделает процесс celery worker (запущен отдельно).
        result = fetch_snapshot_task.delay(name)

        self.stdout.write(
            self.style.SUCCESS(
                f"Задача поставлена в очередь: task_id={result.id}. "
                f"Статус можно проверить через API или `celery -A config result {result.id}`."
            )
        )
