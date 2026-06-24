import pytest
from src.crypto import Coin


@pytest.fixture
def btc():
    return Coin(
        name="Bitcoin",
        symbol="BTC",
        current_price=100_000,
        price_change_percentage_24h=5.5,
        market_cap=2_000_000,
        total_volume=500_000,
    )


@pytest.fixture
def eth():
    return Coin(
        name="Ethereum",
        symbol="ETH",
        current_price=5_000,
        price_change_percentage_24h=2.5,
        market_cap=1_000_000,
        total_volume=300_000,
    )

@pytest.fixture
def coins(btc, eth):
    return [btc, eth]