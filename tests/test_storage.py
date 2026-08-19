import sqlite3

import pytest

from src.storage import SqliteStorage, connect


def test_sqlite_storage_creates_tables(connection):

    SqliteStorage(connection)

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        """
    )

    tables = {
        row[0]
        for row in cursor.fetchall()
    }

    assert "snapshots" in tables
    assert "coin_prices" in tables


def test_sqlite_storage_save(connection, report):

    storage = SqliteStorage(connection)

    storage.save(report)

    cursor = connection.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM snapshots"
    )

    snapshots = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM coin_prices"
    )

    coins = cursor.fetchone()[0]

    assert snapshots == 1
    assert coins == 2


def test_sqlite_storage_accumulates_snapshots(connection, report):

    storage = SqliteStorage(connection)

    storage.save(report)
    storage.save(report)

    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM snapshots")

    assert cursor.fetchone()[0] == 2


def test_foreign_key_is_enforced(connection):
    """PRAGMA foreign_keys включён, поэтому ссылка на несуществующий снимок падает."""

    SqliteStorage(connection)

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO coin_prices
            (snapshot_id, name, symbol, price)
            VALUES (?, ?, ?, ?)
            """,
            (999, "Bitcoin", "BTC", 100_000)
        )


def test_connect_closes_connection():
    """connect() закрывает соединение на выходе, а не только транзакцию."""

    with connect(":memory:") as connection:
        connection.execute("SELECT 1")

    with pytest.raises(sqlite3.ProgrammingError):
        connection.execute("SELECT 1")
