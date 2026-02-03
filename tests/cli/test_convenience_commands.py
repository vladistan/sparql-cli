"""Tests for convenience commands (Phase 5: classes, predicates)."""

import pytest
from typer.testing import CliRunner

from sparql.cli.main import app
from sparql.core.exit_codes import ExitCode
from tests.conftest import WIKIDATA_ENDPOINT

runner = CliRunner()


# =============================================================================
# Classes Command Tests (Step 5.1)
# =============================================================================


def test_classes_help_shows_options():
    result = runner.invoke(app, ["classes", "--help"])

    assert result.exit_code == ExitCode.SUCCESS
    assert "--limit" in result.stdout or "-n" in result.stdout
    assert "--endpoint" in result.stdout or "-E" in result.stdout


def test_classes_with_invalid_profile_fails():
    result = runner.invoke(
        app,
        ["classes", "--profile", "nonexistent_profile_xyz"],
    )

    # Should fail with config error for unknown profile
    assert result.exit_code == ExitCode.CONFIG_ERROR


@pytest.mark.integration
def test_classes_returns_distinct_classes():
    result = runner.invoke(
        app,
        ["classes", "--endpoint", WIKIDATA_ENDPOINT, "--limit", "5", "--timeout", "90"],
    )

    # May be rate limited by Wikidata (429), accept network errors as flaky
    if result.exit_code == ExitCode.NETWORK_ERROR:
        pytest.skip("Wikidata rate limited (HTTP 429)")

    assert result.exit_code == ExitCode.SUCCESS
    # Should return data (classes are URIs or abbreviated with prefixes)
    assert "http" in result.stdout.lower() or "class" in result.stdout.lower()


@pytest.mark.integration
def test_classes_respects_limit():
    result = runner.invoke(
        app,
        [
            "classes",
            "--endpoint",
            WIKIDATA_ENDPOINT,
            "--limit",
            "3",
            "--format",
            "jsonl",
        ],
    )

    assert result.exit_code == ExitCode.SUCCESS
    # Count lines (JSONL = one object per line)
    lines = [ln for ln in result.stdout.strip().split("\n") if ln]
    assert len(lines) <= 3


@pytest.mark.integration
def test_classes_default_limit_is_100():
    result = runner.invoke(
        app,
        [
            "classes",
            "--endpoint",
            WIKIDATA_ENDPOINT,
            "--format",
            "jsonl",
            "--timeout",
            "120",
        ],
    )

    assert result.exit_code == ExitCode.SUCCESS
    lines = [ln for ln in result.stdout.strip().split("\n") if ln]
    # Default limit 100, may return fewer if endpoint has fewer
    assert len(lines) <= 100


@pytest.mark.integration
def test_classes_respects_format_option():
    result = runner.invoke(
        app,
        ["classes", "--endpoint", WIKIDATA_ENDPOINT, "--limit", "2", "--format", "csv"],
    )

    assert result.exit_code == ExitCode.SUCCESS
    # CSV has header row
    assert "class" in result.stdout.lower()


def test_classes_connection_error_returns_network_code():
    invalid_endpoint = "http://invalid-endpoint-xyz.invalid/sparql"
    result = runner.invoke(
        app,
        ["classes", "--endpoint", invalid_endpoint],
    )

    assert result.exit_code == ExitCode.NETWORK_ERROR


# =============================================================================
# Predicates Command Tests (Step 5.2)
# =============================================================================


def test_predicates_help_shows_options():
    result = runner.invoke(app, ["predicates", "--help"])

    assert result.exit_code == ExitCode.SUCCESS
    assert "--limit" in result.stdout or "-n" in result.stdout
    assert "--endpoint" in result.stdout or "-E" in result.stdout


def test_predicates_with_invalid_profile_fails():
    result = runner.invoke(
        app,
        ["predicates", "--profile", "nonexistent_profile_xyz"],
    )

    assert result.exit_code == ExitCode.CONFIG_ERROR


@pytest.mark.integration
def test_predicates_returns_distinct_predicates():
    result = runner.invoke(
        app,
        ["predicates", "--endpoint", WIKIDATA_ENDPOINT, "--limit", "5"],
    )

    assert result.exit_code == ExitCode.SUCCESS
    # Should return data (predicates are URIs)
    assert "http" in result.stdout.lower() or "predicate" in result.stdout.lower()


@pytest.mark.integration
def test_predicates_respects_limit():
    result = runner.invoke(
        app,
        [
            "predicates",
            "--endpoint",
            WIKIDATA_ENDPOINT,
            "--limit",
            "3",
            "--format",
            "jsonl",
        ],
    )

    assert result.exit_code == ExitCode.SUCCESS
    lines = [ln for ln in result.stdout.strip().split("\n") if ln]
    assert len(lines) <= 3


@pytest.mark.integration
def test_predicates_respects_format_option():
    result = runner.invoke(
        app,
        [
            "predicates",
            "--endpoint",
            WIKIDATA_ENDPOINT,
            "--limit",
            "2",
            "--format",
            "csv",
        ],
    )

    assert result.exit_code == ExitCode.SUCCESS
    assert "predicate" in result.stdout.lower()


def test_predicates_connection_error_returns_network_code():
    invalid_endpoint = "http://invalid-endpoint-xyz.invalid/sparql"
    result = runner.invoke(
        app,
        ["predicates", "--endpoint", invalid_endpoint],
    )

    assert result.exit_code == ExitCode.NETWORK_ERROR


# =============================================================================
# Shared Option Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.parametrize("command", ["classes", "predicates"])
def test_convenience_commands_work_with_explicit_endpoint(command):
    # Test that commands work when endpoint is explicitly provided
    result = runner.invoke(
        app,
        [command, "--endpoint", WIKIDATA_ENDPOINT, "--limit", "2"],
    )

    assert result.exit_code == ExitCode.SUCCESS


@pytest.mark.parametrize("command", ["classes", "predicates"])
def test_convenience_commands_show_in_main_help(command):
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == ExitCode.SUCCESS
    assert command in result.stdout


# =============================================================================
# Explore Command Tests (Step 5.3)
# =============================================================================

# Well-known Wikidata URI for testing (Douglas Adams)
TEST_URI = "http://www.wikidata.org/entity/Q42"


def test_explore_help_shows_uri_argument():
    result = runner.invoke(app, ["explore", "--help"])

    assert result.exit_code == ExitCode.SUCCESS
    assert "URI" in result.stdout or "uri" in result.stdout
    assert "--limit" in result.stdout or "-n" in result.stdout
    assert "--endpoint" in result.stdout or "-E" in result.stdout


def test_explore_requires_uri_argument():
    result = runner.invoke(app, ["explore", "--endpoint", WIKIDATA_ENDPOINT])

    # Should fail without URI argument
    assert result.exit_code != ExitCode.SUCCESS


def test_explore_with_invalid_profile_fails():
    result = runner.invoke(
        app,
        ["explore", TEST_URI, "--profile", "nonexistent_profile_xyz"],
    )

    assert result.exit_code == ExitCode.CONFIG_ERROR


@pytest.mark.integration
def test_explore_returns_triples_for_uri():
    result = runner.invoke(
        app,
        ["explore", TEST_URI, "--endpoint", WIKIDATA_ENDPOINT, "--limit", "5"],
    )

    assert result.exit_code == ExitCode.SUCCESS
    # Should return triples with s, p, o columns (may be abbreviated with prefixes)
    output_lower = result.stdout.lower()
    # URIs in output - either full http:// or abbreviated prefix:localname format
    assert "http" in output_lower or ":" in output_lower


@pytest.mark.integration
def test_explore_respects_limit():
    result = runner.invoke(
        app,
        [
            "explore",
            TEST_URI,
            "--endpoint",
            WIKIDATA_ENDPOINT,
            "--limit",
            "3",
            "--format",
            "jsonl",
        ],
    )

    assert result.exit_code == ExitCode.SUCCESS
    lines = [ln for ln in result.stdout.strip().split("\n") if ln]
    assert len(lines) <= 3


@pytest.mark.integration
def test_explore_respects_format_option():
    result = runner.invoke(
        app,
        [
            "explore",
            TEST_URI,
            "--endpoint",
            WIKIDATA_ENDPOINT,
            "--limit",
            "2",
            "--format",
            "csv",
        ],
    )

    assert result.exit_code == ExitCode.SUCCESS
    # CSV should have header with s, p, o columns
    first_line = result.stdout.split("\n")[0].lower()
    assert "s" in first_line or "p" in first_line or "o" in first_line


def test_explore_connection_error_returns_network_code():
    invalid_endpoint = "http://invalid-endpoint-xyz.invalid/sparql"
    result = runner.invoke(
        app,
        ["explore", TEST_URI, "--endpoint", invalid_endpoint],
    )

    assert result.exit_code == ExitCode.NETWORK_ERROR


def test_explore_shows_in_main_help():
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == ExitCode.SUCCESS
    assert "explore" in result.stdout
