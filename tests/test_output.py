from src.crypto import JsonStorage
from src.crypto import ConsoleOutput
from src.crypto import CsvStorage
from src.crypto import FileOutput
from src.crypto import OUTPUTS


def test_json_output(mocker):
    mock_open = mocker.mock_open()
    mocker.patch("builtins.open", mock_open)
    storage = JsonStorage("test.json")
    report = {"coins_count": 2}
    storage.save(report)
    mock_open.assert_called_once_with("test.json", "w", encoding="utf-8")


def test_console_output(mocker):
    mock_console = mocker.Mock()
    output = ConsoleOutput(console=mock_console)
    report = {
        "top_up": [
            {"name": "Bitcoin", "price_change_percentage_24h": 5.5}
        ],
        "top_down": [
            {"name": "Ethereum", "price_change_percentage_24h": 2.5}
        ],
        "volume_leader": {
            "name": "Bitcoin",
            "total_volume": 500000
        },
        "market_cap": 3000000
    }
    output.save(report)
    mock_console.print.assert_called_once()


def test_csv_output(mocker):
    mock_open = mocker.mock_open()
    mocker.patch("builtins.open", mock_open)
    storage = CsvStorage("test.csv")
    report = {
        "generated_at": "2026-01-01",
        "coins_count": 2,
        "market_cap": 3000000
    }
    storage.save(report)
    mock_open.assert_called_once_with("test.csv", "w", newline="", encoding="utf-8")


def test_output_polymorphism(mocker):

    mocker.patch("builtins.open", mocker.mock_open())

    mock_console = mocker.Mock()

    outputs = [
        ConsoleOutput(mock_console),
        FileOutput(mock_console, JsonStorage()),
        FileOutput(mock_console, CsvStorage()),
    ]

    report = {
        "top_up": [],
        "top_down": [],
        "volume_leader": {"name": "BTC", "total_volume": 1000},
        "market_cap": 1000000,
        "generated_at": "2026-01-01",
        "coins_count": 2,
    }

    for out in outputs:
        out.save(report)

    assert mock_console.print.call_count == 3


def test_outputs_registry_has_all_formats():
    assert set(OUTPUTS) == {"console", "json", "csv"}


def test_json_output_writes_file(mocker):
    mock_open = mocker.mock_open()
    mocker.patch("builtins.open", mock_open)
    mock_console = mocker.Mock()
    output = FileOutput(mock_console, JsonStorage("test.json"))
    output.save({"coins_count": 2})
    mock_open.assert_called_once_with("test.json", "w", encoding="utf-8")
    mock_console.print.assert_called_once()


def test_csv_output_writes_file(mocker):
    mock_open = mocker.mock_open()
    mocker.patch("builtins.open", mock_open)
    mock_console = mocker.Mock()
    output = FileOutput(mock_console, CsvStorage("test.csv"))
    report = {
        "generated_at": "2026-01-01",
        "coins_count": 2,
        "market_cap": 3000000
    }
    output.save(report)
    mock_open.assert_called_once_with("test.csv", "w", newline="", encoding="utf-8")
    mock_console.print.assert_called_once()








