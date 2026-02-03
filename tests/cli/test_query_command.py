"""Tests for query command (Step 2.4)."""

import pytest
from typer.testing import CliRunner

from sparql.cli.main import app
from sparql.core.exit_codes import ExitCode

runner = CliRunner()

# Wikidata requires descriptive User-Agent
WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"


SIMPLE_QUERY = "SELECT * WHERE { ?s ?p ?o } LIMIT 1"


@pytest.mark.integration
def test_query_executes_inline_query():
    result = runner.invoke(
        app,
        ["query", "--endpoint", WIKIDATA_ENDPOINT, "-e", SIMPLE_QUERY],
    )

    assert result.exit_code == ExitCode.SUCCESS
    assert "http" in result.stdout.lower()


@pytest.mark.integration
def test_query_executes_file_query(temp_query_file):
    result = runner.invoke(
        app,
        ["query", "--endpoint", WIKIDATA_ENDPOINT, str(temp_query_file)],
    )

    assert result.exit_code == ExitCode.SUCCESS


@pytest.mark.integration
def test_query_with_timeout_option():
    args = [
        "query", "--endpoint", WIKIDATA_ENDPOINT,
        "--timeout", "60", "-e", SIMPLE_QUERY,
    ]
    result = runner.invoke(app, args)

    assert result.exit_code == ExitCode.SUCCESS


def test_query_missing_endpoint_fails():
    result = runner.invoke(
        app,
        ["query", "-e", "SELECT * WHERE { ?s ?p ?o }"],
    )

    # Should fail because endpoint is required
    assert result.exit_code != ExitCode.SUCCESS


def test_query_missing_query_source_fails():
    result = runner.invoke(
        app,
        ["query", "--endpoint", WIKIDATA_ENDPOINT],
    )

    # Should fail because no query provided
    assert result.exit_code == ExitCode.INPUT_ERROR


def test_query_nonexistent_file_fails(temp_dir):
    result = runner.invoke(
        app,
        ["query", "--endpoint", WIKIDATA_ENDPOINT, str(temp_dir / "nonexistent.rq")],
    )

    assert result.exit_code == ExitCode.INPUT_ERROR
    # Error message goes to stderr which is included in output
    assert "not found" in result.output.lower()


def test_query_connection_error_returns_network_code():
    invalid_endpoint = "http://invalid-endpoint-xyz.invalid/sparql"
    result = runner.invoke(
        app,
        ["query", "--endpoint", invalid_endpoint, "-e", "SELECT * WHERE { ?s ?p ?o }"],
    )

    assert result.exit_code == ExitCode.NETWORK_ERROR


@pytest.mark.integration
def test_query_invalid_sparql_returns_error():
    result = runner.invoke(
        app,
        ["query", "--endpoint", WIKIDATA_ENDPOINT, "-e", "THIS IS NOT VALID SPARQL"],
    )

    # HTTP error from endpoint
    assert result.exit_code == ExitCode.NETWORK_ERROR


def test_query_help_shows_options():
    result = runner.invoke(app, ["query", "--help"])

    assert result.exit_code == ExitCode.SUCCESS
    assert "--endpoint" in result.stdout
    assert "--timeout" in result.stdout
    assert "-e" in result.stdout or "--execute" in result.stdout
