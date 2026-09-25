import logging

from django.db import IntegrityError, transaction
from django.db.models import Avg, Max, Min, Sum

from crypto.models import CoinPrice, Snapshot, WatchlistItem, normalize_symbol
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


def _latest_snapshot():
    """Последний снимок как подзапрос — отдельным обращением к базе не выполняется."""
    return Snapshot.objects.order_by('-created_at').values('pk')[:1]


def market_stats():
    """Мин/макс/средняя цена и суммарная капитализация по последнему снимку."""
    return CoinPrice.objects.filter(snapshot__in=_latest_snapshot()).aggregate(
        min_price=Min('price'),
        max_price=Max('price'),
        avg_price=Avg('price'),
        total_market_cap=Sum('market_cap'),
    )


def top_movers(limit=10):
    """Топ по росту цены за 24 часа; монеты без данных об изменении не участвуют."""
    return (
        CoinPrice.objects
        .filter(snapshot__in=_latest_snapshot(), price_change_24h__isnull=False)
        .order_by('-price_change_24h')[:limit]
    )