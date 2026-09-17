from rest_framework import viewsets
from .models import Snapshot, CoinPrice
from .serializers import SnapshotSerializer, SnapshotDetailSerializer, CoinHistorySerializer


class SnapshotViewSet(viewsets.ModelViewSet):
    queryset = Snapshot.objects.all()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SnapshotDetailSerializer
        return SnapshotSerializer


class CoinPriceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CoinHistorySerializer

    def get_queryset(self):
        queryset = CoinPrice.objects.all().order_by('-snapshot__created_at')
        symbol = self.request.query_params.get('symbol')
        if symbol:
            queryset = queryset.filter(symbol__iexact=symbol)
        return queryset