from django.db.models import Count
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .models import CoinPrice, Snapshot
from .serializers import (
    CoinHistorySerializer,
    SnapshotDetailSerializer,
    SnapshotSerializer,
    WatchlistItemSerializer,
)


class SnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Snapshot.objects.annotate(prices_count=Count('prices')).order_by('-created_at', '-id')
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SnapshotDetailSerializer
        return SnapshotSerializer


class CoinPriceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CoinHistorySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = CoinPrice.objects.select_related('snapshot').order_by('-snapshot__created_at')
        symbol = self.request.query_params.get('symbol')
        if symbol:
            queryset = queryset.filter(symbol__iexact=symbol)
        return queryset


class WatchlistViewSet(viewsets.GenericViewSet):
    serializer_class = WatchlistItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_value_regex = r'\d+'

    def list(self, request):
        items = services.list_watchlist(request.user)
        page = self.paginate_queryset(items)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            item = services.add_to_watchlist(
                request.user, serializer.validated_data['symbol']
            )
        except services.SymbolNotFound:
            return Response(
                {'detail': 'Символ не найден на бирже.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except services.AlreadyInWatchlist:
            return Response(
                {'detail': 'Монета уже в списке.'},
                status=status.HTTP_409_CONFLICT,
            )
        except services.ExchangeUnavailable:
            return Response(
                {'detail': 'Биржа недоступна, попробуйте позже.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(self.get_serializer(item).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        try:
            services.remove_from_watchlist(request.user, pk)
        except services.WatchlistItemNotFound:
            return Response(
                {'detail': 'Не найдено.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)


class MarketStatsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(services.market_stats())
