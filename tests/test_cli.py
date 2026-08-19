import pytest
from typer.testing import CliRunner

from src.crypto import app
from src.settings import settings
from src.storage import SqliteStorage, connect


runner = CliRunner()


@pytest.fixture
def database(mocker, tmp_path, report):
    """Файл БД с одним снимком, на который смотрит settings.database."""

    path = tmp_path / "snapshots.db"

    with connect(str(path)) as connection:
        SqliteStorage(connection).save(report)

    mocker.patch.object(settings, "database", str(path))

    return path


def test_unknown_source_lists_available_options():
    """APIS[source] без проверки роняет голый KeyError с трейсбеком."""

    result = runner.invoke(app, ["run", "--source", "binance"])

    assert result.exit_code != 0
    assert "coingecko" in result.output
    assert "KeyError" not in result.output


def test_unknown_output_lists_available_options():
    """То же самое для OUTPUTS[output]."""

    result = runner.invoke(app, ["run", "--output", "xml"])

    assert result.exit_code != 0
    assert "console" in result.output
    assert "KeyError" not in result.output


def test_list_snapshots_without_database_leaves_no_file(mocker, tmp_path):
    """sqlite3.connect() создаёт пустой файл на месте отсутствующей базы,
    поэтому команда должна отказаться до соединения и не насорить."""

    path = tmp_path / "missing.db"
    mocker.patch.object(settings, "database", str(path))

    result = runner.invoke(app, ["list-snapshots"])

    assert result.exit_code == 1
    assert not path.exists()


def test_list_snapshots_shows_saved_snapshots(database):
    """Счастливый путь: проверка базы не ломает обычный вывод."""

    result = runner.invoke(app, ["list-snapshots"])

    assert result.exit_code == 0
