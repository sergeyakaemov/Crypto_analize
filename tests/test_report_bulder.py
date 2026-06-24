from src.crypto import ReportBuilder

def test_report_builder(coins):
    builder = ReportBuilder()
    top_up = coins
    top_down = list(reversed(coins))
    volume = coins[0]

    report = builder.build(
        data=coins,
        top_up=top_up,
        top_down=top_down,
        volume=volume,
        market_cap=3_000_000
    )

    assert report["coins_count"] ==  2
    assert report["market_cap"] == 3_000_000


