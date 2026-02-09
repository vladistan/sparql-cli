"""Tests for the SPARQL update CLI command."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from sparql.cli.main import app
from sparql.core.models import UpdateResult

runner = CliRunner()


def test_update_command_help():
    result = runner.invoke(app, ["update", "--help"])
    assert result.exit_code == 0
    assert "SPARQL UPDATE" in result.output or "update" in result.output.lower()


@patch("sparql.cli.commands.update.SPARQLClient")
@patch("sparql.cli.commands.update.load_config")
@patch("sparql.cli.commands.update.resolve_config")
def test_update_command_executes_inline(mock_resolve, mock_load, mock_client_cls):
    mock_resolved = MagicMock()
    mock_resolved.endpoint = "https://example.com/sparql/query"
    mock_resolved.update_endpoint = "https://example.com/sparql/update"
    mock_resolved.timeout = 30.0
    mock_resolved.user_agent = "test/1.0"
    mock_resolved.username = None
    mock_resolved.password = None
    mock_resolved.auth_type = MagicMock()
    mock_resolved.auth_type.value = "none"
    mock_resolved.http_method = MagicMock()
    mock_resolved.http_method.value = "POST"
    mock_resolve.return_value = mock_resolved
    mock_load.return_value = MagicMock()

    mock_client = MagicMock()
    mock_client.execute_update.return_value = UpdateResult(
        success=True, status_code=200, message="OK"
    )
    mock_client_cls.return_value = mock_client

    result = runner.invoke(
        app,
        ["update", "-e", "INSERT DATA { <http://ex.org/s> <http://ex.org/p> 'val' }"],
    )

    assert result.exit_code == 0
    assert "successful" in result.output.lower() or "200" in result.output


@patch("sparql.cli.commands.update.SPARQLClient")
@patch("sparql.cli.commands.update.load_config")
@patch("sparql.cli.commands.update.resolve_config")
def test_update_command_reports_failure(mock_resolve, mock_load, mock_client_cls):
    mock_resolved = MagicMock()
    mock_resolved.endpoint = "https://example.com/sparql/query"
    mock_resolved.update_endpoint = "https://example.com/sparql/update"
    mock_resolved.timeout = 30.0
    mock_resolved.user_agent = "test/1.0"
    mock_resolved.username = None
    mock_resolved.password = None
    mock_resolved.auth_type = MagicMock()
    mock_resolved.auth_type.value = "none"
    mock_resolved.http_method = MagicMock()
    mock_resolved.http_method.value = "POST"
    mock_resolve.return_value = mock_resolved
    mock_load.return_value = MagicMock()

    mock_client = MagicMock()
    mock_client.execute_update.return_value = UpdateResult(
        success=False, status_code=400, message="Bad syntax"
    )
    mock_client_cls.return_value = mock_client

    result = runner.invoke(
        app,
        ["update", "-e", "INVALID UPDATE"],
    )

    assert result.exit_code != 0


def test_update_command_requires_input():
    result = runner.invoke(app, ["update"])
    assert result.exit_code != 0


@patch("sparql.cli.commands.update.SPARQLClient")
@patch("sparql.cli.commands.update.load_config")
@patch("sparql.cli.commands.update.resolve_config")
def test_update_command_reads_from_file(
    mock_resolve, mock_load, mock_client_cls, tmp_path
):
    update_file = tmp_path / "test.ru"
    update_file.write_text(
        "INSERT DATA { <http://ex.org/s> <http://ex.org/p> 'val' }"
    )

    mock_resolved = MagicMock()
    mock_resolved.endpoint = "https://example.com/sparql/query"
    mock_resolved.update_endpoint = "https://example.com/sparql/update"
    mock_resolved.timeout = 30.0
    mock_resolved.user_agent = "test/1.0"
    mock_resolved.username = None
    mock_resolved.password = None
    mock_resolved.auth_type = MagicMock()
    mock_resolved.auth_type.value = "none"
    mock_resolved.http_method = MagicMock()
    mock_resolved.http_method.value = "POST"
    mock_resolve.return_value = mock_resolved
    mock_load.return_value = MagicMock()

    mock_client = MagicMock()
    mock_client.execute_update.return_value = UpdateResult(
        success=True, status_code=200, message="OK"
    )
    mock_client_cls.return_value = mock_client

    result = runner.invoke(app, ["update", str(update_file)])

    assert result.exit_code == 0
    mock_client.execute_update.assert_called_once()
