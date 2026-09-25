from .views import SnapshotViewSet, CoinPriceViewSet, WatchlistViewSet, MarketStatsView
from django.urls import path, include
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'snapshots', SnapshotViewSet)
router.register(r'coins', CoinPriceViewSet, basename='coinprice')
router.register(r'watchlist', WatchlistViewSet, basename='watchlist')

urlpatterns = [
    path('analytics/market-stats/', MarketStatsView.as_view(), name='market-stats'),
    path('', include(router.urls)),
]
