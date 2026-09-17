import pytest
import requests


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    """Любой реальный HTTP-запрос в тестах — ошибка."""
    def fail(*args, **kwargs):
        raise RuntimeError("Реальный HTTP-запрос в тестах запрещён")

    monkeypatch.setattr(requests, "get", fail)


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(username="alice", password="pass12345")


@pytest.fixture
def other_user(django_user_model):
    return django_user_model.objects.create_user(username="bob", password="pass12345")


@pytest.fixture
def provider(mocker):
    """Фальшивая биржа: по умолчанию любой символ существует."""
    provider = mocker.Mock()
    provider.symbol_exists.return_value = True
    mocker.patch("crypto.services.get_provider", return_value=provider)
    return provider