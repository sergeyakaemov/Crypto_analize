from typing import Any

from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    response = exception_handler(exc, context)
    if response is None:
        return None

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
