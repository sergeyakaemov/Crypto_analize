from django.core.management import BaseCommand, CommandError
from django.db import transaction
import requests

from crypto.models import CoinPrice, Snapshot
from crypto.retry import retry
from crypto.sources import SOURCES


@retry(max_attempts=3, delay=2)
def fetch(source):
    response = requests.get(
        source.URL,
        params=source.params(),
        headers=source.headers(),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


class Command(BaseCommand):
    help = "Загружает цены монет с биржи и сохраняет снимок"

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            choices=SOURCES,
            default="coingecko",
            help="Источник данных",
        )

    def handle(self, *args, **options):
        source = SOURCES[options["source"]]()

        try:
            data = fetch(source)
        except requests.RequestException as error:
            raise CommandError(f"Не удалось получить данные: {error}")

        rows = source.normalize(data)

        with transaction.atomic():
            snapshot = Snapshot.objects.create(source=options["source"])
            CoinPrice.objects.bulk_create([
                CoinPrice(snapshot=snapshot, **row)
                for row in rows
            ])

        self.stdout.write(
            self.style.SUCCESS(
                f"Снимок #{snapshot.pk}: сохранено {len(rows)} монет"
            )
        )