from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    SnapshotViewSet,
    CoinPriceViewSet,
    WatchlistViewSet,
    MarketStatsView,
    TopMoversView,
    VolumeLeadersView,
    SnapshotCollectView,
    TaskStatusView,
)


router = DefaultRouter()
router.register(r'snapshots', SnapshotViewSet)
router.register(r'coins', CoinPriceViewSet, basename='coinprice')
router.register(r'watchlist', WatchlistViewSet, basename='watchlist')

urlpatterns = [
    path('analytics/market-stats/', MarketStatsView.as_view(), name='market-stats'),
    path('analytics/top-movers/', TopMoversView.as_view(), name='top-movers'),
    path('snapshots/collect/', SnapshotCollectView.as_view(), name='snapshot-collect'),
    path('tasks/<str:task_id>/', TaskStatusView.as_view(), name='task-status'),
    path('', include(router.urls)),
    path('analytics/volume-leaders/', VolumeLeadersView.as_view(), name='volume-leaders'),
]
