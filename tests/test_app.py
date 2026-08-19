from src.crypto import Coin, CryptoApp, CryptoProcessor, ReportBuilder


def build_app(mocker, coins, top=2):
    """CryptoApp на настоящих процессоре и сборщике отчёта.

    Внешние зависимости — клиент, API, хранилище, вывод — заглушки:
    проверяем именно то, какие списки монет уходят в расчёты.
    """
    api = mocker.Mock()
    api.normalize.return_value = coins

    return CryptoApp(
        client=mocker.Mock(),
        api=api,
        processor=CryptoProcessor(),
        report_builder=ReportBuilder(),
        output=mocker.Mock(),
        storage=mocker.Mock(),
        console=mocker.Mock(),
        top=top,
    )


def saved_report(app):
    app.run()
    return app.storage.save.call_args[0][0]


def test_report_counts_coins_without_price_change(mocker):
    """Монета, которой API не отдал изменение цены, не участвует в топах,
    но обязана попасть в сумму капитализации, в счётчик и в поиск лидера
    по объёму: иначе отчёт занижает рынок."""

    coins = [
        Coin("Alpha", "a", 1, 5.0, 50, 10),
        Coin("Beta", "b", 1, -2.0, 50, 10),
        Coin("Gamma", "g", 1, None, 900, 999),
    ]

    report = saved_report(build_app(mocker, coins))

    assert report["market_cap"] == 1000
    assert report["coins_count"] == 3
    assert report["volume_leader"]["symbol"] == "g"


def test_tops_skip_coins_without_price_change(mocker):
    """В топах сортировка идёт по изменению цены, поэтому монеты
    без него туда попадать не должны."""

    coins = [
        Coin("Alpha", "a", 1, 5.0, 50, 10),
        Coin("Beta", "b", 1, -2.0, 50, 10),
        Coin("Gamma", "g", 1, None, 900, 999),
    ]

    report = saved_report(build_app(mocker, coins))

    for group in ("top_up", "top_down"):
        assert all(
            coin["price_change_percentage_24h"] is not None
            for coin in report[group]
        )
