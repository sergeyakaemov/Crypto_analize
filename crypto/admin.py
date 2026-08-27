from django.contrib import admin

from .models import CoinPrice, Snapshot


class CoinPriceInline(admin.TabularInline):
    model = CoinPrice
    extra = 0


@admin.register(Snapshot)
class SnapshotAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'source')
    inlines = [CoinPriceInline]


@admin.register(CoinPrice)
class CoinPriceAdmin(admin.ModelAdmin):
    list_display = ('symbol','name', 'price', 'price_change_24h', 'snapshot')