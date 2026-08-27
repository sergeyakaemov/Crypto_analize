from .views import SnapshotViewSet
from django.urls import path, include
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'snapshots', SnapshotViewSet)

urlpatterns = [
    path('', include(router.urls)),
]