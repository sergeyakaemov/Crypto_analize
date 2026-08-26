from django.core.management import BaseCommand
import requests
from crypto.models import CoinPrice, Snapshot
from crypto.sources import SOURCES


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

        response = requests.get(
            source.URL,
            params=source.params(),
            headers=source.headers(),
            timeout=30,
        )
        response.raise_for_status()

        rows = source.normalize(response.json())

        snapshot = Snapshot.objects.create()

        CoinPrice.objects.bulk_create([
            CoinPrice(snapshot=snapshot, **row)
            for row in rows
        ])

        self.stdout.write(
            self.style.SUCCESS(
                f"Снимок #{snapshot.pk}: сохранено {len(rows)} монет"
            )
        )
