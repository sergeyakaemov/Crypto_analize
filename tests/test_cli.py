from typer.testing import CliRunner

from src.crypto import app


runner = CliRunner()


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