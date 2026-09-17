import time

import requests


def retry(max_attempts=3, delay=2):
    """Повторяет запрос при временных сбоях, но не при ошибках 4xx."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_error = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except requests.HTTPError as error:
                    if 400 <= error.response.status_code < 500:
                        raise
                    last_error = error
                except requests.RequestException as error:
                    last_error = error

                if attempt < max_attempts:
                    time.sleep(delay)

            raise requests.RequestException(
                f"Не удалось выполнить запрос после {max_attempts} попыток"
            ) from last_error

        return wrapper

    return decorator