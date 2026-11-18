from typing import Any

from django.urls import reverse

API_VERSION = "v1"


def api_reverse(view_name: str, **kwargs: Any) -> str:
    return reverse(view_name, kwargs={"version": API_VERSION, **kwargs})
