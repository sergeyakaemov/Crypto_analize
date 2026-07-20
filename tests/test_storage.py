import sqlite3

from src.storage import SqliteStorage

import pytest


@pytest.fixture
def report():
    return {
        "generated_at": "2026-07-20T10:00:00",
        "coins_count": 2,
        "coins": [
            {
                "name": "Bitcoin",
                "symbol": "BTC",
                "current_price": 100000,
                "price_change_percentage_24h": 5.5,
                "market_cap": 2000000,
                "total_volume": 500000
            },
            {
                "name": "Ethereum",
                "symbol": "ETH",
                "current_price": 3000,
                "price_change_percentage_24h": -2.1,
                "market_cap": 1000000,
                "total_volume": 200000
            }
        ]
    }


def test_sqlite_storage_creates_tables(tmp_path):

    db = tmp_path / "test.db"

    storage = SqliteStorage(db)

    with sqlite3.connect(db) as conn:

        cursor = conn.cursor()

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


def test_sqlite_storage_save(report, tmp_path):

    db = tmp_path / "test.db"

    storage = SqliteStorage(db)

    storage.save(report)


    with sqlite3.connect(db) as conn:

        cursor = conn.cursor()

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