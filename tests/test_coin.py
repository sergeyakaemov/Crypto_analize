def test_coin_creation(btc):
    assert btc.name == "Bitcoin"
    assert btc.symbol == "BTC"
    assert btc.current_price == 100_000


def test_coin_repr(btc):
    assert repr(btc) == "Bitcoin (BTC)"


def test_coin_to_dict(btc):
    result = btc.to_dict()

    assert result["name"] == "Bitcoin"
    assert result["symbol"] == "BTC"
    assert result["current_price"] == 100_000


def test_coin_gt(btc, eth):
    assert btc > eth


def test_coin_lt(eth, btc):
    assert eth < btc