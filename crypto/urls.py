from .views import SnapshotViewSet, CoinPriceViewSet, WatchlistViewSet, MarketStatsView, TopMoversView
from django.urls import path, include
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'snapshots', SnapshotViewSet)
router.register(r'coins', CoinPriceViewSet, basename='coinprice')
router.register(r'watchlist', WatchlistViewSet, basename='watchlist')

urlpatterns = [
    path('analytics/market-stats/', MarketStatsView.as_view(), name='market-stats'),
    path('analytics/top-movers/', TopMoversView.as_view(), name='top-movers'),
    path('', include(router.urls)),
]
