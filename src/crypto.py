import os
import requests
import json
from datetime import datetime
import typer
import csv
from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv
from abc import ABC, abstractmethod
import time
from src.settings import settings, StorageType
from src.storage import (BaseStorage, JsonStorage, CsvStorage,)


def retry(max_attempts=3, delay=2):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except requests.RequestException as error:
                    print(
                        "Ошибка: "
                        + str(error)
                        + ". Попытка "
                        + str(attempt + 1)
                        + "/"
                        + str(max_attempts)
                    )
                    time.sleep(delay)
            raise requests.RequestException(
                "Не удалось выполнить запрос после "
                + str(max_attempts)
                + " попыток"
            )

        return wrapper

    return decorator


class BaseAPI(ABC):
    URL = str

    @abstractmethod
    def get_params(self):
        pass

    @abstractmethod
    def get_headers(self):
        pass

    @abstractmethod
    def normalize(self, data):
        pass


class APIClient:

    @retry(max_attempts=3, delay=2)
    def get_data(self, url, headers=None, params=None):
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()


class CoinGeckoAPI(BaseAPI):

    URL = "https://api.coingecko.com/api/v3/coins/markets"

    def get_params(self):
        return {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 50,
            "page": 1,
        }

    def get_headers(self):
        return None

    def normalize(self, data):
        return [
            Coin(
                name=c["name"],
                symbol=c["symbol"],
                current_price=c["current_price"],
                price_change_percentage_24h=c["price_change_percentage_24h"],
                market_cap=c["market_cap"],
                total_volume=c["total_volume"],
            )
            for c in data
        ]


class CoinMarketCapAPI(BaseAPI):

    URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"

    def get_params(self):
        return {
            "start": "1",
            "limit": 10,
            "convert": "USD",
        }

    def get_headers(self):
        return {
            "Accept": "application/json",
            "X-CMC_PRO_API_KEY": os.getenv("COINMARKETCAP_API_KEY"),
        }

    def normalize(self, data):
        return [
            Coin(
                name=c["name"],
                symbol=c["symbol"],
                current_price=c["quote"]["USD"]["price"],
                price_change_percentage_24h=c["quote"]["USD"]["percent_change_24h"],
                market_cap=c["quote"]["USD"]["market_cap"],
                total_volume=c["quote"]["USD"]["volume_24h"],
            )
            for c in data["data"]
        ]


class CryptoProcessor:

    def filter_coins_with_price_change(self, data):
        return [c for c in data if c.price_change_percentage_24h is not None]

    def get_top_price_changes(self, data, limit=3, reverse=True):
        return sorted(
            data,
            key=lambda c: c.price_change_percentage_24h,
            reverse=reverse,
        )[:limit]

    def top_total_volume(self, data):
        return max(data, key=lambda c: c.total_volume)

    def total_market_cap(self, data):
        return sum(c.market_cap for c in data)


class Coin:
    def __init__(
        self,
        name,
        symbol,
        current_price,
        price_change_percentage_24h,
        market_cap,
        total_volume,
    ):
        self.name = name
        self.symbol = symbol
        self.current_price = current_price
        self.price_change_percentage_24h = price_change_percentage_24h
        self.market_cap = market_cap
        self.total_volume = total_volume

    def __lt__(self, other):
        return self.market_cap < other.market_cap

    def __gt__(self, other):
        return self.market_cap > other.market_cap

    def __repr__(self):
        return f"{self.name} ({self.symbol})"

    def to_dict(self):
        return self.__dict__


class BaseOutput(ABC):

    @abstractmethod
    def save(self, report: dict):
        pass


class ConsoleOutput(BaseOutput):

    def __init__(self, console):
        self.console = console

    def save(self, report: dict):
        table = Table(title="[bold]Крипто мониторинг рынка[/bold]")
        table.add_column("[bold]ТОП лидеров роста[/bold]")
        table.add_column("[bold]ТОП лидеров падения[/bold]")
        table.add_column("[bold]Лидер по объёму торгов[/bold]")
        table.add_column("[bold]Суммарная капитализация 50 монет[/bold]")

        top_up = "\n".join(
            f"{c['name']} {c['price_change_percentage_24h']} %"
            for c in report["top_up"]
        )

        top_down = "\n".join(
            f"{c['name']} {c['price_change_percentage_24h']} %"
            for c in report["top_down"]
        )

        volume = (
            f"{report['volume_leader']['name']} "
            f"${report['volume_leader']['total_volume']}"
        )

        table.add_row(
            f"[green]{top_up}[/green]",
            f"[red]{top_down}[/red]",
            f"[yellow]{volume}[/yellow]",
            f"[blue]${report['market_cap']}[/blue]",
        )

        self.console.print(table)


class ReportBuilder:

    def build(self, data, top_up, top_down, volume, market_cap):
        return {
            "generated_at": datetime.now().isoformat(),
            "coins_count": len(data),
            "market_cap": market_cap,
            "coins": [c.to_dict() for c in data],
            "top_up": [c.to_dict() for c in top_up],
            "top_down": [c.to_dict() for c in top_down],
            "volume_leader": volume.to_dict(),
        }


class CryptoApp:

    def __init__(
        self,
        client,
        api,
        processor,
        report_builder,
        output,
        storage,
        console,
        top,
    ):
        self.client = client
        self.api = api
        self.processor = processor
        self.report_builder = report_builder
        self.output = output
        self.storage = storage
        self.console = console
        self.top = top

    def __enter__(self):
        return self

    def run(self):

        raw = self.client.get_data(
            self.api.URL,
            headers=self.api.get_headers(),
            params=self.api.get_params(),
        )

        data = self.api.normalize(raw)

        clean = self.processor.filter_coins_with_price_change(data)

        top_up = self.processor.get_top_price_changes(
            clean,
            limit=self.top,
            reverse=True,
        )

        top_down = self.processor.get_top_price_changes(
            clean,
            limit=self.top,
            reverse=False,
        )

        volume = self.processor.top_total_volume(clean)
        market_cap = self.processor.total_market_cap(clean)

        report = self.report_builder.build(
            clean,
            top_up,
            top_down,
            volume,
            market_cap,
        )

        # Сначала сохраняем
        self.storage.save(report)

        # Затем отображаем
        self.output.save(report)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.console.print(f"[red]Ошибка: {exc_val}[/red]")
        return False


app = typer.Typer()

APIS = {
    "coingecko": CoinGeckoAPI,
    "coinmarketcap": CoinMarketCapAPI,
}

OUTPUTS = {
    "console": ConsoleOutput,
}

from src.storage import (
    JsonStorage,
    CsvStorage,
    SqliteStorage,
)


STORAGES = {
    StorageType.JSON: JsonStorage,
    StorageType.SQLITE: SqliteStorage,
}


@app.command()
def run(
    source: str = "coingecko",
    output: str = "console",
    top: int = 3,
):

    load_dotenv()

    console = Console()

    client = APIClient()

    api_class = APIS[source]
    api = api_class()

    output_class = OUTPUTS[output]
    output_instance = output_class(console)

    processor = CryptoProcessor()
    report_builder = ReportBuilder()

    storage_class = STORAGES[settings.storage]
    storage = storage_class()

    with CryptoApp(
        client,
        api,
        processor,
        report_builder,
        output_instance,
        storage,
        console,
        top,
    ) as app:
        app.run()


if __name__ == "__main__":
    app()


# Выбор ресурсов:
# --source coingecko
# --source coinmarketcap

# Формат вывода:
# --output console

# Количество топов:
# --top 3
# --top 5
# --top 10