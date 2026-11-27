import logging
from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.defaults import page_not_found
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Монета уже в списке."
    default_code = "conflict"


class ServiceUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Биржа недоступна, попробуйте позже."
    default_code = "service_unavailable"


logger = logging.getLogger(__name__)


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    response = exception_handler(exc, context)
    if response is None:
        logger.error("Необработанная ошибка API", exc_info=exc)
        return Response(
            {"error": "Внутренняя ошибка сервера.", "code": "server_error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if isinstance(exc, ValidationError):
        response.data = {
            "error": "Некорректные данные.",
            "code": "invalid",
            "details": response.data,
        }
        return response

    detail = response.data["detail"]
    response.data = {"error": str(detail), "code": detail.code}
    return response


def api_page_not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    """404 для путей, не совпавших ни с одним маршрутом.

    До DRF такой запрос не доходит, поэтому api_exception_handler его не видит.
    Для /api/ отвечаем в общем формате ошибок, для остального — стандартной
    HTML-страницей Django.
    """
    if request.path.startswith("/api/"):
        return JsonResponse(
            {"error": "Не найдено.", "code": "not_found"},
            status=404,
            json_dumps_params={"ensure_ascii": False},
        )
    return page_not_found(request, exception)
