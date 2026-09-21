import logging

from django.db import IntegrityError, transaction

from crypto.models import WatchlistItem, normalize_symbol
from crypto.sources import ProviderError, get_provider

logger = logging.getLogger(__name__)


class WatchlistError(Exception):
    """Базовая ошибка watchlist."""


class SymbolNotFound(WatchlistError):
    """Биржа ответила, что такого символа нет."""


class AlreadyInWatchlist(WatchlistError):
    """Монета уже есть в списке пользователя."""


class ExchangeUnavailable(WatchlistError):
    """Биржа не ответила — существование символа неизвестно."""


class WatchlistItemNotFound(WatchlistError):
    """Элемента нет или он принадлежит другому пользователю."""


def list_watchlist(user):
    return WatchlistItem.objects.filter(user=user)


def add_to_watchlist(user, symbol):
    symbol = normalize_symbol(symbol)

    if WatchlistItem.objects.filter(user=user, symbol=symbol).exists():
        raise AlreadyInWatchlist(symbol)

    try:
        exists = get_provider().symbol_exists(symbol)
    except ProviderError as error:
        logger.warning("Биржа не ответила при проверке символа %s: %s", symbol, error)
        raise ExchangeUnavailable(symbol) from error

    if not exists:
        raise SymbolNotFound(symbol)

    try:
        with transaction.atomic():
            return WatchlistItem.objects.create(user=user, symbol=symbol)
    except IntegrityError:
        raise AlreadyInWatchlist(symbol)


def remove_from_watchlist(user, item_id):
    deleted, _ = WatchlistItem.objects.filter(user=user, pk=item_id).delete()
    if not deleted:
        raise WatchlistItemNotFound(item_id)
