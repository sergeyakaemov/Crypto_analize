import contextlib
import csv
import json
import sqlite3
from abc import ABC, abstractmethod


@contextlib.contextmanager
def connect(db_name):
    """Открывает соединение с SQLite и гарантированно закрывает его.

    with sqlite3.connect(...) закрывает транзакцию, но не само соединение,
    поэтому закрываем явно в finally. PRAGMA foreign_keys включается на
    каждом соединении: по умолчанию SQLite внешние ключи не проверяет.
    """
    connection = sqlite3.connect(db_name)

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        yield connection
    finally:
        connection.close()


class BaseStorage(ABC):

    @abstractmethod
    def save(self, report: dict) -> None:
        pass


class JsonStorage(BaseStorage):

    def __init__(self, filename="report.json"):
        self.filename = filename

    def save(self, report: dict) -> None:
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4, ensure_ascii=False)


class CsvStorage(BaseStorage):

    def __init__(self, filename="report.csv"):
        self.filename = filename

    def save(self, report: dict) -> None:
        with open(self.filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            writer.writerow(["metric", "value"])
            writer.writerow(["generated_at", report["generated_at"]])
            writer.writerow(["coins_count", report["coins_count"]])
            writer.writerow(["market_cap", report["market_cap"]])


class SqliteStorage(BaseStorage):
    """Принимает готовое соединение.

    Сам его не открывает и не закрывает: этим управляет вызывающий код
    через connect(). Благодаря этому тесты передают сюда
    sqlite3.connect(":memory:") и работают с той же базой, что и аналитика.
    """

    def __init__(self, connection):
        self.connection = connection
        self.create_tables()

    def create_tables(self) -> None:
        with self.connection:
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    coins_count INTEGER NOT NULL
                )
            """)

            self.connection.execute("""
            CREATE TABLE IF NOT EXISTS coin_prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    price REAL,
                    price_change REAL,
                    market_cap REAL,
                    total_volume REAL,

                    FOREIGN KEY(snapshot_id)
                    REFERENCES snapshots(id)
                )
            """)

    def save(self, report: dict) -> None:
        with self.connection:
            cursor = self.connection.cursor()

            cursor.execute("""
                INSERT INTO snapshots
                (created_at, coins_count)
                VALUES (?, ?)
                """,
                (report["generated_at"], report["coins_count"],)
            )
            snapshot_id = cursor.lastrowid

            for coin in report["coins"]:

                cursor.execute(
                    """
                    INSERT INTO coin_prices
                    (
                        snapshot_id,
                        name,
                        symbol,
                        price,
                        price_change,
                        market_cap,
                        total_volume
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        snapshot_id,
                        coin["name"],
                        coin["symbol"],
                        coin["current_price"],
                        coin["price_change_percentage_24h"],
                        coin["market_cap"],
                        coin["total_volume"],
                    )
                )
