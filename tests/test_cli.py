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


def test_compare_snapshots_rejects_equal_ids(database):
    """Сравнение снимка с самим собой даёт колонку нулей,
    которая выглядит как «рынок замер»."""

    result = runner.invoke(app, ["compare-snapshots", "1", "1"])

    assert result.exit_code == 1


def test_compare_snapshots_reports_missing_ids(database):
    """Несуществующий id раньше давал пустой вывод без объяснений."""

    result = runner.invoke(app, ["compare-snapshots", "1", "7"])

    assert result.exit_code == 1
    assert "7" in result.output


def test_compare_snapshots_shows_direction(mocker, tmp_path, make_coin, make_report):
    """Счастливый путь: проверки не мешают, а направление сравнения
    печатается явно — знак разницы зависит от порядка id."""

    path = tmp_path / "two.db"

    with connect(str(path)) as connection:
        storage = SqliteStorage(connection)
        storage.save(make_report([make_coin(price=100)]))
        storage.save(make_report([make_coin(price=105)]))

    mocker.patch.object(settings, "database", str(path))

    result = runner.invoke(app, ["compare-snapshots", "1", "2"])

    assert result.exit_code == 0
    assert "Снимок 1 -> снимок 2" in result.output


def test_list_snapshots_shows_saved_snapshots(database):
    """Счастливый путь: проверка базы не ломает обычный вывод."""

    result = runner.invoke(app, ["list-snapshots"])

    assert result.exit_code == 0
