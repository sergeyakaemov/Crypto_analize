import pytest
from src.crypto import Coin
from src.storage import connect


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


@pytest.fixture
def connection():
    """База в памяти: создаётся на каждый тест и исчезает после него."""
    with connect(":memory:") as conn:
        yield conn


@pytest.fixture
def make_coin():
    """Фабрика монеты для отчёта: цена и изменение задаются параметрами."""
    def make(
        symbol="BTC",
        name="Bitcoin",
        price=100_000,
        price_change=5.0,
        market_cap=2_000_000,
        total_volume=500_000,
    ):
        return {
            "name": name,
            "symbol": symbol,
            "current_price": price,
            "price_change_percentage_24h": price_change,
            "market_cap": market_cap,
            "total_volume": total_volume,
        }

    return make


@pytest.fixture
def make_report():
    """Фабрика отчёта: набор монет и время снимка задаются параметрами."""
    def make(coins, generated_at="2026-07-20T10:00:00"):
        return {
            "generated_at": generated_at,
            "coins_count": len(coins),
            "market_cap": sum(c["market_cap"] for c in coins),
            "coins": list(coins),
        }

    return make


@pytest.fixture
def report(make_coin, make_report):
    """Готовый отчёт из двух монет — самый частый случай в тестах."""
    return make_report([
        make_coin("BTC", "Bitcoin", price=100_000, price_change=5.5),
        make_coin(
            "ETH",
            "Ethereum",
            price=3_000,
            price_change=-2.1,
            market_cap=1_000_000,
            total_volume=200_000,
        ),
    ])
