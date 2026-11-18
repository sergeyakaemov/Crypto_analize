from typing import Any, cast

from celery.result import AsyncResult
from django.contrib.auth.models import User
from django.db.models import Count, Sum
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework import filters, permissions, serializers, status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.views import APIView

from . import services
from .filters import CoinPriceFilter
from .models import CoinPrice, Snapshot
from .pagination import CoinCursorPagination
from .permissions import IsAdminOrReadOnly
from .serializers import (
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
    queryset = Snapshot.objects.annotate(
        prices_count=Count("prices"),
        total_market_cap=Sum("prices__market_cap", default=0),
    ).order_by("-created_at", "-id")
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["created_at", "total_market_cap"]

    def get_serializer_class(self) -> type[BaseSerializer]:
        if self.action == "retrieve":
            return SnapshotDetailSerializer
        return SnapshotSerializer


class CoinPriceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CoinPrice.objects.select_related("snapshot")
    serializer_class = CoinHistorySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = CoinPriceFilter
    search_fields = ["symbol", "name"]
    pagination_class = CoinCursorPagination


class WatchlistViewSet(viewsets.GenericViewSet):
    serializer_class = WatchlistItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_value_regex = r"\d+"

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        items = services.list_watchlist(cast(User, request.user))
        page = self.paginate_queryset(items)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
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

    def destroy(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> Response:
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

    @extend_schema(summary="Статистика рынка", responses=MarketStatsSerializer)
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return Response(MarketStatsSerializer(services.market_stats()).data)


class TopMoversView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(summary="Лидеры роста", responses=CoinPriceSerializer(many=True))
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return Response(CoinPriceSerializer(services.top_movers(), many=True).data)


class VolumeLeadersView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Лидеры по объёму торгов", responses=CoinPriceSerializer(many=True)
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return Response(CoinPriceSerializer(services.volume_leaders(), many=True).data)


class SnapshotCollectView(APIView):
    """Ставит в очередь задачу сбора снимка. Не делает работу сама —
    вся логика живёт в crypto.tasks.fetch_snapshot_task."""

    permission_classes = [IsAdminOrReadOnly]

    @extend_schema(
        summary="Запуск сбора снимка",
        request=SnapshotCollectSerializer,
        responses={
            202: inline_serializer(
                name="SnapshotCollectQueued",
                fields={
                    "task_id": serializers.CharField(),
                    "status": serializers.CharField(),
                },
            ),
            400: OpenApiResponse(
                description="source не из списка: coingecko / coinmarketcap"
            ),
            401: OpenApiResponse(description="Нет JWT-токена или он недействителен."),
            403: OpenApiResponse(
                description="Пользователь авторизован, но не администратор (is_staff)."
            ),
        },
        examples=[
            OpenApiExample(
                "Сбор из Сoingecko",
                value={"source": "coingecko"},
                request_only=True,
            ),
            OpenApiExample(
                "Задача поставлена в очередь",
                value={
                    "task_id": "5b1e6a8c-2f0d-4c7e-9a43-1d2b3c4d5e6f",
                    "status": "PENDING",
                },
                response_only=True,
                status_codes=["202"],
            ),
        ],
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
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

    @extend_schema(
        summary="Статус задачи",
        responses={
            200: inline_serializer(
                name="TaskStatus",
                fields={
                    "task_id": serializers.CharField(),
                    "status": serializers.CharField(),
                    "result": serializers.JSONField(required=False),
                    "error": serializers.CharField(required=False),
                },
            ),
        },
        examples=[
            OpenApiExample(
                "Задача ещё выполняется",
                value={
                    "task_id": "5b1e6a8c-2f0d-4c7e-9a43-1d2b3c4d5e6f",
                    "status": "PENDING",
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "Снимок собран",
                value={
                    "task_id": "5b1e6a8c-2f0d-4c7e-9a43-1d2b3c4d5e6f",
                    "status": "SUCCESS",
                    "result": {
                        "snapshot_id": 42,
                        "coins_count": 100,
                        "source": "coingecko",
                    },
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "Задача упала",
                value={
                    "task_id": "5b1e6a8c-2f0d-4c7e-9a43-1d2b3c4d5e6f",
                    "status": "FAILURE",
                    "error": "HTTPError: 404 Client Error",
                },
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def get(
        self, request: Request, task_id: str, *args: Any, **kwargs: Any
    ) -> Response:
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
