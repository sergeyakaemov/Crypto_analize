import pytest


from crypto import services, sources
from crypto.models import WatchlistItem

pytestmark = pytest.mark.django_db


def test_normalize_symbol():
    assert services.normalize_symbol("  btc ") == "BTC"


def test_add_saves_normalized_symbol(user, provider):
    item = services.add_to_watchlist(user, " btc ")

    assert item.symbol == "BTC"
    assert item.user == user
    provider.symbol_exists.assert_called_once_with("BTC")


def test_add_unknown_symbol_raises_and_saves_nothing(user, provider):
    provider.symbol_exists.return_value = False

    with pytest.raises(services.SymbolNotFound):
        services.add_to_watchlist(user, "zzz")

    assert not WatchlistItem.objects.exists()


def test_add_duplicate_raises_without_exchange_call(user, provider):
    WatchlistItem.objects.create(user=user, symbol="BTC")

    with pytest.raises(services.AlreadyInWatchlist):
        services.add_to_watchlist(user, "btc")

    provider.symbol_exists.assert_not_called()


def test_model_normalizes_symbol_on_save(user):
    item = WatchlistItem.objects.create(user=user, symbol=" btc ")

    item.refresh_from_db()
    assert item.symbol == "BTC"


def test_duplicate_written_past_service_is_caught(user, provider):
    """Строка заведена мимо сервиса — нормализация в save() всё равно ловит дубль."""
    WatchlistItem.objects.create(user=user, symbol="btc")

    with pytest.raises(services.AlreadyInWatchlist):
        services.add_to_watchlist(user, "BTC")

    provider.symbol_exists.assert_not_called()


def test_add_when_exchange_down_raises_unavailable(user, provider):
    provider.symbol_exists.side_effect = sources.ProviderError("таймаут")

    with pytest.raises(services.ExchangeUnavailable):
        services.add_to_watchlist(user, "BTC")

    assert not WatchlistItem.objects.exists()


def test_concurrent_add_becomes_already_in_watchlist(user, provider):
    def add_concurrently(symbol):
        WatchlistItem.objects.create(user=user, symbol=symbol)
        return True

    provider.symbol_exists.side_effect = add_concurrently

    with pytest.raises(services.AlreadyInWatchlist):
        services.add_to_watchlist(user, "BTC")

    assert WatchlistItem.objects.count() == 1


def test_same_symbol_allowed_for_different_users(user, other_user, provider):
    services.add_to_watchlist(user, "BTC")
    services.add_to_watchlist(other_user, "BTC")

    assert WatchlistItem.objects.filter(symbol="BTC").count() == 2


def test_list_returns_only_own_items(user, other_user):
    own = WatchlistItem.objects.create(user=user, symbol="BTC")
    WatchlistItem.objects.create(user=other_user, symbol="ETH")

    assert list(services.list_watchlist(user)) == [own]


def test_remove_deletes_own_item(user):
    item = WatchlistItem.objects.create(user=user, symbol="BTC")

    services.remove_from_watchlist(user, item.pk)

    assert not WatchlistItem.objects.exists()


def test_remove_foreign_item_raises_and_keeps_it(user, other_user):
    item = WatchlistItem.objects.create(user=other_user, symbol="BTC")

    with pytest.raises(services.WatchlistItemNotFound):
        services.remove_from_watchlist(user, item.pk)

    assert WatchlistItem.objects.filter(pk=item.pk).exists()


def test_remove_missing_item_raises(user):
    with pytest.raises(services.WatchlistItemNotFound):
        services.remove_from_watchlist(user, 999)