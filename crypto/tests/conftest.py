import pytest
import requests

from crypto.models import CoinPrice, Snapshot


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    """Любой реальный HTTP-запрос в тестах — ошибка."""
    def fail(*args, **kwargs):
        raise RuntimeError("Реальный HTTP-запрос в тестах запрещён")

    monkeypatch.setattr(requests.sessions.Session, "request", fail)


@pytest.fixture(autouse=True)
def fast_password_hasher(settings):
    """Быстрый хешер паролей: PBKDF2 намеренно медленный, в тестах это лишнее."""
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(username="alice", password="pass12345")


@pytest.fixture
def other_user(django_user_model):
    return django_user_model.objects.create_user(username="bob", password="pass12345")


@pytest.fixture
def provider(mocker):
    """Фальшивая биржа: по умолчанию любой символ существует."""
    provider = mocker.Mock()
    provider.symbol_exists.return_value = True
    mocker.patch("crypto.services.get_provider", return_value=provider)
    return provider


COIN_DEFAULTS = {
    "price": 1,
    "price_change_24h": 0,
    "market_cap": 1,
    "total_volume": 1,
}


@pytest.fixture
def make_snapshot(db):
    """Фабрика снимка. Поля монет передаются списками: price=[1, 2] — две монеты
    с ценами 1 и 2, остальные поля из COIN_DEFAULTS. coins=N — N монет по умолчанию."""
    def make(coins=0, **fields):
        count = len(next(iter(fields.values()))) if fields else coins
        snapshot = Snapshot.objects.create(source="coingecko")
        CoinPrice.objects.bulk_create(
            CoinPrice(
                snapshot=snapshot,
                **{
                    "name": f"Coin {number}",
                    "symbol": f"C{number}",
                    **COIN_DEFAULTS,
                    **{field: values[number] for field, values in fields.items()},
                },
            )
            for number in range(count)
        )
        return snapshot

    return make
