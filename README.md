# Крипто-анализатор

Django-приложение, которое периодически забирает цены монет с биржи
(CoinGecko или CoinMarketCap) и сохраняет **снимки рынка** — состояние на
конкретный момент времени. По накопленным снимкам REST API отдаёт цены,
аналитику и динамику, а пользователи ведут свой список отслеживаемых монет.

Стек: Django, Django REST Framework, PostgreSQL, Celery + Redis,
JWT-аутентификация, документация OpenAPI (drf-spectacular).

## Требования

- Python 3.12+
- PostgreSQL
- Redis — брокер для фоновых задач Celery (на Windows подойдёт Memurai)

## Установка для разработки

Команды для PowerShell (Windows):

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Заполнить `.env` (см. таблицу ниже), затем:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Фоновые задачи (каждая команда в отдельном терминале, Redis должен быть запущен):

```bash
celery -A config worker -l info --pool=solo
celery -A config beat -l info
```

`--pool=solo` нужен только на Windows: стандартный пул процессов Celery там не работает.

## Переменные окружения

Хранятся в `.env` (не попадает в git), образец — `.env.example`.

| Переменная | Назначение | По умолчанию |
|---|---|---|
| `DJANGO_SECRET_KEY` | секретный ключ Django | — (обязательна) |
| `DJANGO_DEBUG` | режим отладки: `True` или `False` | `False` |
| `DJANGO_ALLOWED_HOSTS` | разрешённые хосты через запятую | `localhost,127.0.0.1` |
| `POSTGRES_PASSWORD` | пароль пользователя `postgres` | — |
| `EXCHANGE_PROVIDER` | биржа: `coingecko` или `coinmarketcap` | `coingecko` |
| `COINMARKETCAP_API_KEY` | ключ CoinMarketCap (если выбрана эта биржа) | — |
| `CELERY_BROKER_URL` | адрес брокера задач | `redis://localhost:6379/0` |
| `CELERY_RESULT_BACKEND` | хранилище результатов задач | `redis://localhost:6379/1` |

`DJANGO_DEBUG` по умолчанию выключен: если на сервере забыть задать переменную,
отладочные страницы с кодом и настройками не откроются посторонним.

## Запуск в продакшен-режиме

Приложение запускается через WSGI-сервер Gunicorn с `DEBUG=False`.
Gunicorn работает только в Linux и macOS; на Windows — через WSL
(достаточно WSL 1: он видит PostgreSQL и Redis Windows по `localhost`).

В Linux / WSL, из корня проекта, с активированным виртуальным окружением:

```bash
pip install -r requirements.txt
python manage.py collectstatic --noinput
DJANGO_DEBUG=False gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 2
```

- `collectstatic` собирает статику всех приложений (админка, Swagger, DRF) в папку `staticfiles/`;
- при `DEBUG=False` Django сам статику не отдаёт — её раздаёт Whitenoise (middleware сразу после `SecurityMiddleware`);
- `DJANGO_DEBUG=False` перед командой действует только на этот запуск и важнее значения из `.env`;
- debug_toolbar подключается только при `DEBUG=True`.

## Тесты

```bash
python -m pytest crypto/tests -q
```

## Документация API

Все эндпоинты находятся под префиксом `/api/v1/`.

- Swagger UI: http://127.0.0.1:8000/api/v1/docs/
- OpenAPI-схема: http://127.0.0.1:8000/api/v1/schema/

Для защищённых эндпоинтов получить токен через `POST /api/v1/token/`
(логин и пароль пользователя), в Swagger нажать **Authorize** и вставить значение `access`.
Обновление токена — `POST /api/v1/token/refresh/`.

### Формат ошибок

Все ошибки API (400, 401, 403, 404, 429, 500) возвращаются в одном формате:

```json
{"error": "Сообщение об ошибке.", "code": "error_code"}
```

Для ошибок валидации (400) добавляется ключ `details` с ошибками по каждому полю.
