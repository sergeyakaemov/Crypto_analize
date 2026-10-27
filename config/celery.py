import os

from celery import Celery

# Говорим Celery, где искать настройки Django, ДО создания Celery-приложения —
# иначе app.config_from_object ниже не найдёт CELERY_* переменные.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# namespace='CELERY' значит: в settings.py все параметры Celery называются
# CELERY_BROKER_URL, CELERY_RESULT_BACKEND и т.д. — Celery сам отрежет префикс.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Ищет файлы tasks.py во всех INSTALLED_APPS (в т.ч. в нашем приложении crypto)
# и регистрирует все @shared_task из них — вручную импортировать не нужно.
app.autodiscover_tasks()
