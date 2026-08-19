from src.crypto import CryptoProcessor, Coin
import pytest


def test_total_market_cap(coins):
    processor = CryptoProcessor()
    result = processor.total_market_cap(coins)
    assert result == 3_000_000


def test_total_volume(coins):
    processor = CryptoProcessor()
    result = processor.top_total_volume(coins)
    assert result.name == "Bitcoin"


@pytest.mark.parametrize("reverse, expected_first",[(True, "Bitcoin"),(False, "Ethereum")])
def test_get_top_price_changes(coins, reverse, expected_first):
    processor = CryptoProcessor()
    result = processor.get_top_price_changes(coins, reverse=reverse)
    assert result[0].name == expected_first


def test_filter_coins_with_price_change():
    processor = CryptoProcessor()
    coins = [
        Coin("Bitcoin", "BTC", 100, 5.5, 2_000_000, 500_000),
        Coin("Ethereum", "ETH", 50, None, 1_000_000, 300_000),
    ]

    result = processor.filter_coins_with_price_change(coins)
    assert len(result) == 1
    assert result[0].name == "Bitcoin"





