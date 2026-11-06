from typing import cast

from celery.result import AsyncResult
from django.contrib.auth.models import User
from django.db.models import Count, QuerySet
from rest_framework import permissions, status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.views import APIView

from . import services
from .models import CoinPrice, Snapshot
from .serializers import (
    CoinFilterSerializer,
    CoinHistorySerializer,
    CoinPriceSerializer,
    MarketStatsSerializer,
    SnapshotCollectSerializer,
    SnapshotDetailSerializer,
    SnapshotSerializer,
    WatchlistItemSerializer,
)
from .tasks import fetch_snapshot_task


class SnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Snapshot.objects.annotate(prices_count=Count("prices")).order_by(
        "-created_at", "-id"
    )
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self) -> type[BaseSerializer]:
        if self.action == "retrieve":
            return SnapshotDetailSerializer
        return SnapshotSerializer


class CoinPriceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CoinHistorySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self) -> QuerySet[CoinPrice]:
        filters = CoinFilterSerializer(data=self.request.query_params)
        filters.is_valid(raise_exception=True)
        return services.filter_coins(**filters.validated_data)


class WatchlistViewSet(viewsets.GenericViewSet):
    serializer_class = WatchlistItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_value_regex = r"\d+"

    def list(self, request: Request) -> Response:
        items = services.list_watchlist(cast(User, request.user))
        page = self.paginate_queryset(items)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            item = services.add_to_watchlist(
                cast(User, request.user), serializer.validated_data["symbol"]
            )
        except services.SymbolNotFound:
            return Response(
                {"detail": "Символ не найден на бирже."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except services.AlreadyInWatchlist:
            return Response(
                {"detail": "Монета уже в списке."},
                status=status.HTTP_409_CONFLICT,
            )
        except services.ExchangeUnavailable:
            return Response(
                {"detail": "Биржа недоступна, попробуйте позже."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(self.get_serializer(item).data, status=status.HTTP_201_CREATED)

    def destroy(self, request: Request, pk: str) -> Response:
        try:
            services.remove_from_watchlist(cast(User, request.user), pk)
        except services.WatchlistItemNotFound:
            return Response(
                {"detail": "Не найдено."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)


class MarketStatsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request: Request) -> Response:
        return Response(MarketStatsSerializer(services.market_stats()).data)


class TopMoversView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request: Request) -> Response:
        return Response(CoinPriceSerializer(services.top_movers(), many=True).data)


class VolumeLeadersView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request: Request) -> Response:
        return Response(CoinPriceSerializer(services.volume_leaders(), many=True).data)


class SnapshotCollectView(APIView):
    """Ставит в очередь задачу сбора снимка. Не делает работу сама —
    вся логика живёт в crypto.tasks.fetch_snapshot_task."""

    permission_classes = [permissions.AllowAny]

    def post(self, request: Request) -> Response:
        # Проверяем запрос ДО постановки в очередь: неверный вход пользователя
        # разумно отбивать сразу синхронным 400, не тратя время воркера и не
        # пряча ошибку внутрь асинхронной задачи.
        serializer = SnapshotCollectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = fetch_snapshot_task.delay(serializer.validated_data.get("source"))

        # 202 Accepted: запрос принят к обработке, но ресурс (снимок) ещё
        # не создан — задача могла даже не начать выполняться к моменту
        # этого ответа. Тело ответа поэтому не Snapshot, а идентификатор
        # задачи, по которому можно спросить результат отдельно.
        return Response(
            {"task_id": result.id, "status": result.status},
            status=status.HTTP_202_ACCEPTED,
        )


class TaskStatusView(APIView):
    """Статус и результат произвольной Celery-задачи по её task_id."""

    permission_classes = [permissions.AllowAny]

    def get(self, request: Request, task_id: str) -> Response:
        result = AsyncResult(task_id)

        payload = {"task_id": task_id, "status": result.status}

        if result.ready():
            if result.successful():
                payload["result"] = result.result
            else:
                # В случае ошибки result.result — это сам объект исключения,
                # а не JSON-сериализуемые данные, поэтому отдаём его как текст.
                payload["error"] = str(result.result)

        return Response(payload)
