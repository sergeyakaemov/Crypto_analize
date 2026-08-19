from src.storage import SqliteStorage
from src.sqlite_analytics import SqliteAnalytics


def test_list_snapshots(connection, make_coin, make_report):

    storage = SqliteStorage(connection)

    storage.save(make_report([make_coin()]))

    analytics = SqliteAnalytics(connection)

    snapshots = analytics.list_snapshots()

    assert len(snapshots) == 1
    assert snapshots[0][2] == 1


def test_price_history(connection, make_coin, make_report):

    storage = SqliteStorage(connection)

    storage.save(
        make_report(
            [make_coin(price=100_000)],
            generated_at="2026-07-20T10:00:00",
        )
    )

    storage.save(
        make_report(
            [make_coin(price=105_000)],
            generated_at="2026-07-20T11:00:00",
        )
    )

    analytics = SqliteAnalytics(connection)

    history = analytics.price_history("BTC")

    assert len(history) == 2
    assert history[0][2] == 100_000
    assert history[1][2] == 105_000


def test_compare_snapshots(connection, make_coin, make_report):

    storage = SqliteStorage(connection)

    storage.save(
        make_report(
            [make_coin(price=100_000)],
            generated_at="2026-07-20T10:00:00",
        )
    )

    storage.save(
        make_report(
            [make_coin(price=105_000)],
            generated_at="2026-07-20T11:00:00",
        )
    )

    analytics = SqliteAnalytics(connection)

    result = analytics.compare_snapshots(1, 2)

    assert len(result) == 1

    assert result[0][0] == "BTC"
    assert result[0][1] == 100_000
    assert result[0][2] == 105_000
    assert result[0][3] == 5_000


def test_top_price_changes(connection, make_coin, make_report):

    storage = SqliteStorage(connection)

    storage.save(
        make_report([
            make_coin("BTC", "Bitcoin", price=100_000, price_change=10),
            make_coin("ETH", "Ethereum", price=3_000, price_change=-5),
            make_coin("SOL", "Solana", price=200, price_change=7),
        ])
    )

    analytics = SqliteAnalytics(connection)

    result = analytics.top_price_changes()

    assert result[0][0] == "BTC"
    assert result[1][0] == "SOL"

    result_down = analytics.top_price_changes(reverse=False)

    assert result_down[0][0] == "ETH"
