import sqlite3

from src.storage import SqliteStorage
from src.sqlite_analytics import SqliteAnalytics


def test_list_snapshots(tmp_path):

    db = tmp_path / "test.db"

    storage = SqliteStorage(db)

    report = {
        "generated_at": "2026-07-20T10:00:00",
        "coins_count": 1,
        "coins": [
            {
                "name": "Bitcoin",
                "symbol": "BTC",
                "current_price": 100000,
                "price_change_percentage_24h": 5,
                "market_cap": 2000000,
                "total_volume": 500000
            }
        ]
    }


    storage.save(report)


    analytics = SqliteAnalytics(db)

    snapshots = analytics.list_snapshots()


    assert len(snapshots) == 1
    assert snapshots[0][2] == 1


def test_price_history(tmp_path):

    db = tmp_path / "test.db"

    storage = SqliteStorage(db)


    report1 = {
        "generated_at": "2026-07-20T10:00:00",
        "coins_count": 1,
        "coins": [
            {
                "name": "Bitcoin",
                "symbol": "BTC",
                "current_price": 100000,
                "price_change_percentage_24h": 5,
                "market_cap": 2000000,
                "total_volume": 500000
            }
        ]
    }


    report2 = {
        "generated_at": "2026-07-20T11:00:00",
        "coins_count": 1,
        "coins": [
            {
                "name": "Bitcoin",
                "symbol": "BTC",
                "current_price": 105000,
                "price_change_percentage_24h": 5,
                "market_cap": 2100000,
                "total_volume": 600000
            }
        ]
    }


    storage.save(report1)
    storage.save(report2)


    analytics = SqliteAnalytics(db)

    history = analytics.price_history("BTC")


    assert len(history) == 2
    assert history[0][2] == 100000
    assert history[1][2] == 105000


def test_compare_snapshots(tmp_path):

    db = tmp_path / "test.db"

    storage = SqliteStorage(db)


    report1 = {
        "generated_at": "2026-07-20T10:00:00",
        "coins_count": 1,
        "coins": [
            {
                "name": "Bitcoin",
                "symbol": "BTC",
                "current_price": 100000,
                "price_change_percentage_24h": 5,
                "market_cap": 2000000,
                "total_volume": 500000
            }
        ]
    }


    report2 = {
        "generated_at": "2026-07-20T11:00:00",
        "coins_count": 1,
        "coins": [
            {
                "name": "Bitcoin",
                "symbol": "BTC",
                "current_price": 105000,
                "price_change_percentage_24h": 5,
                "market_cap": 2100000,
                "total_volume": 600000
            }
        ]
    }


    storage.save(report1)
    storage.save(report2)


    analytics = SqliteAnalytics(db)

    result = analytics.compare_snapshots(
        1,
        2
    )


    assert len(result) == 1

    assert result[0][0] == "BTC"
    assert result[0][1] == 100000
    assert result[0][2] == 105000
    assert result[0][3] == 5000


def test_top_price_changes(tmp_path):

    db = tmp_path / "test.db"

    storage = SqliteStorage(db)


    report = {
        "generated_at": "2026-07-20T10:00:00",
        "coins_count": 3,
        "coins": [
            {
                "name": "Bitcoin",
                "symbol": "BTC",
                "current_price": 100000,
                "price_change_percentage_24h": 10,
                "market_cap": 2000000,
                "total_volume": 500000
            },
            {
                "name": "Ethereum",
                "symbol": "ETH",
                "current_price": 3000,
                "price_change_percentage_24h": -5,
                "market_cap": 1000000,
                "total_volume": 200000
            },
            {
                "name": "Solana",
                "symbol": "SOL",
                "current_price": 200,
                "price_change_percentage_24h": 7,
                "market_cap": 500000,
                "total_volume": 100000
            }
        ]
    }


    storage.save(report)


    analytics = SqliteAnalytics(db)


    result = analytics.top_price_changes()


    assert result[0][0] == "BTC"
    assert result[1][0] == "SOL"


    result_down = analytics.top_price_changes(
        reverse=False
    )

    assert result_down[0][0] == "ETH"