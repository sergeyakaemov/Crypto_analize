from django.core.management import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings
import requests

from crypto.models import CoinPrice, Snapshot
from crypto.retry import retry
from crypto.client import get_json
from crypto.sources import SOURCES, get_provider


@retry(max_attempts=3, delay=2)
def fetch(source):
    return get_json(
        source.URL,
        params=source.params(),
        headers=source.headers(),
        timeout=30,
    )


class Command(BaseCommand):
    help = "Загружает цены монет с биржи и сохраняет снимок"

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            choices=SOURCES,
            default=None,
            help="Источник данных (по умолчанию EXCHANGE_PROVIDER из .env)",
        )

    def handle(self, *args, **options):
        name = options["source"] or settings.EXCHANGE_PROVIDER
        source = get_provider(name)

        try:
            data = fetch(source)
        except requests.RequestException as error:
            raise CommandError(f"Не удалось получить данные: {error}")

        rows = source.normalize(data)

        with transaction.atomic():
            snapshot = Snapshot.objects.create(source=name)
            CoinPrice.objects.bulk_create([
                CoinPrice(snapshot=snapshot, **row)
                for row in rows
            ])

        self.stdout.write(
            self.style.SUCCESS(
                f"Снимок #{snapshot.pk}: сохранено {len(rows)} монет"
            )
        )