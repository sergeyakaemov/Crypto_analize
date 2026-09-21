import time

import requests

TOO_MANY_REQUESTS = 429

def retry(max_attempts=3, delay=2):
    """Повторяет запрос при временных сбоях; из 4xx повторяет только 429."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_error = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except requests.HTTPError as error:
                    status_code = error.response.status_code
                    if 400 <= status_code < 500 and status_code != TOO_MANY_REQUESTS:
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