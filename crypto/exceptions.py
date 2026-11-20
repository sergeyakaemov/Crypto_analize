import logging
from typing import Any

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
