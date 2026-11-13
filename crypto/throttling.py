from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework.throttling import UserRateThrottle

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.views import APIView


class AdminRateThrottle(UserRateThrottle):
    """Лимит запросов для суперпользователей (scope "admin")."""

    scope = "admin"

    def get_cache_key(self, request: Request, view: APIView) -> str | None:
        if not request.user.is_superuser:
            return None
        return super().get_cache_key(request, view)


class NonAdminUserRateThrottle(UserRateThrottle):
    """Лимит запросов для всех, кроме суперпользователей (scope "user")."""

    def get_cache_key(self, request: Request, view: APIView) -> str | None:
        if request.user.is_superuser:
            return None
        return super().get_cache_key(request, view)
