from django.db import models
from crypto.sources import SOURCES
from django.conf import settings


class Snapshot(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=30, choices=[(k, k) for k in SOURCES])

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'Снимок #{self.pk} от {self.created_at:%d.%m.%Y %H:%M}'


class CoinPrice(models.Model):
    snapshot = models.ForeignKey(Snapshot,
                                 on_delete=models.CASCADE,
                                 related_name='prices')
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=20)
    price = models.DecimalField(decimal_places=12, max_digits=24)
    price_change_24h = models.FloatField(null=True, blank=True)
    market_cap = models.DecimalField(max_digits=20, decimal_places=2)
    total_volume = models.DecimalField(max_digits=20, decimal_places=2)

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=['snapshot', 'symbol'],name='unique_symbol_snapshot')]
    def __str__(self):
        return f"{self.symbol.upper()} — {self.price}"


class WatchlistItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='watchlist',
    )
    symbol = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'symbol'],
                name='unique_user_symbol',
            ),
        ]

    def __str__(self):
        return f'{self.user} — {self.symbol}'