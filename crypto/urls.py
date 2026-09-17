from .views import SnapshotViewSet, CoinPriceViewSet
from django.urls import path, include
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'snapshots', SnapshotViewSet)
router.register(r'coins', CoinPriceViewSet, basename='coinprice')

urlpatterns = [
    path('', include(router.urls)),
]