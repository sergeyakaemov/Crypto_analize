import requests


def get_json(url, params=None, headers=None, timeout=10):
    """Один GET-запрос к API; при HTTP-ошибке бросает requests.HTTPError."""
    response = requests.get(url, params=params, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.json()