"""Query command for executing SPARQL queries against endpoints."""

import sys

import typer

from sparql._version import __version__
from sparql.cli.output import OutputFormat
from sparql.core.client import SPARQLClient
from sparql.core.config import AuthType, load_config, resolve_config
from sparql.core.exceptions import ConfigError, NetworkError
from sparql.core.exceptions import TimeoutError as SPARQLTimeoutError
from sparql.core.exit_codes import ExitCode
from sparql.core.query_source import resolve_query_source
from sparql.formatters import (
    CSVFormatter,
    Formatter,
    JSONFormatter,
    Sparql11Formatter,
    TableFormatter,
    TSVFormatter,
)


def _detect_default_format() -> OutputFormat:
    """Detect default format based on whether stdout is a TTY.

    Returns table for interactive terminal, tsv for piped output.
    """
    if sys.stdout.isatty():
        return OutputFormat.table
    return OutputFormat.tsv


def query(
    query_file: str | None = typer.Argument(  # noqa: B008
        None,
        help="SPARQL query file (.rq) or inline query string",
    ),
    endpoint: str | None = typer.Option(  # noqa: B008
        None,
        "--endpoint",
        "-E",
        help="SPARQL endpoint URL (overrides config)",
    ),
    profile: str | None = typer.Option(  # noqa: B008
        None,
        "--profile",
        "-P",
        help="Use named endpoint profile from config",
    ),
    execute: str | None = typer.Option(  # noqa: B008
        None,
        "--execute",
        "-e",
        help="Execute inline SPARQL query",
    ),
    timeout: float | None = typer.Option(  # noqa: B008
        None,
        "--timeout",
        "-t",
        help="Query timeout in seconds (overrides config)",
    ),
    user: str | None = typer.Option(  # noqa: B008
        None,
        "--user",
        "-u",
        help="Username for authentication (overrides config)",
    ),
    password: str | None = typer.Option(  # noqa: B008
        None,
        "--password",
        "-p",
        help="Password for authentication (overrides config)",
    ),
    digest_auth: bool = typer.Option(  # noqa: B008
        False,
        "--digest",
        help="Use HTTP Digest Authentication instead of Basic",
    ),
    format: OutputFormat | None = typer.Option(  # noqa: B008
        None,
        "--format",
        "-f",
        help="Output format (default: table for TTY, tsv for pipes)",
    ),
    table: bool = typer.Option(  # noqa: B008
        False,
        "--table",
        help="Output as table (shorthand for --format table)",
    ),
    jsonl: bool = typer.Option(  # noqa: B008
        False,
        "--jsonl",
        help="Output as JSONL (one JSON object per line)",
    ),
    compact: bool = typer.Option(  # noqa: B008
        False,
        "--compact",
        help="Compact output (no pretty-print for sparql11 format)",
    ),
    no_header: bool = typer.Option(  # noqa: B008
        False,
        "--no-header",
        help="Skip header row for CSV/TSV output",
    ),
    width: int = typer.Option(  # noqa: B008
        40,
        "--width",
        help="Maximum column width for table format",
    ),
    verbose: bool = typer.Option(  # noqa: B008
        False,
        "--verbose",
        help="Show endpoint and query before execution",
    ),
) -> None:
    """Execute a SPARQL query against an endpoint.

    Query can be provided via file, -e inline, or stdin.
    Endpoint resolved from: CLI flag > env var > profile > default.

    Output format is auto-detected: table for interactive terminals,
    TSV for piped output. Override with --format or shorthand flags.
    """
    stdin = None
    if not sys.stdin.isatty():
        stdin = sys.stdin

    try:
        query_text = resolve_query_source(
            inline=execute,
            file_path=query_file,
            stdin=stdin,
        )
    except ConfigError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(ExitCode.INPUT_ERROR) from e

    # Resolve configuration with precedence
    try:
        config = load_config()
        cli_auth_type = AuthType.DIGEST if digest_auth else None
        resolved = resolve_config(
            config,
            profile=profile,
            cli_endpoint=endpoint,
            cli_timeout=timeout,
            cli_username=user,
            cli_password=password,
            cli_auth_type=cli_auth_type,
        )
    except ConfigError as e:
        typer.echo(f"Config error: {e}", err=True)
        raise typer.Exit(ExitCode.CONFIG_ERROR) from e

    if verbose:
        typer.echo(f"Endpoint: {resolved.endpoint}", err=True)
        typer.echo(f"Timeout: {resolved.timeout}s", err=True)
        typer.echo("Query:", err=True)
        typer.echo(query_text, err=True)
        typer.echo("---", err=True)

    client = SPARQLClient(
        endpoint_url=resolved.endpoint,
        timeout=resolved.timeout,
        user_agent=resolved.user_agent or f"sparql-cli/{__version__}",
        username=resolved.username,
        password=resolved.password,
        digest_auth=resolved.auth_type == AuthType.DIGEST,
    )

    # Resolve output format with precedence:
    # --table > --jsonl > --format > TTY detection
    if table:
        output_format = OutputFormat.table
    elif jsonl:
        output_format = OutputFormat.jsonl
    elif format is not None:
        output_format = format
    else:
        output_format = _detect_default_format()

    # Instantiate formatter with appropriate config
    formatter: Formatter
    if output_format == OutputFormat.json:
        formatter = JSONFormatter(jsonl=False)
    elif output_format == OutputFormat.jsonl:
        formatter = JSONFormatter(jsonl=True)
    elif output_format == OutputFormat.sparql11:
        formatter = Sparql11Formatter(compact=compact)
    elif output_format == OutputFormat.table:
        formatter = TableFormatter(max_width=width)
    elif output_format == OutputFormat.csv:
        formatter = CSVFormatter(skip_header=no_header)
    elif output_format == OutputFormat.tsv:
        formatter = TSVFormatter(skip_header=no_header)
    else:
        formatter = JSONFormatter()

    try:
        results = client.execute(query_text)
        for line in formatter.format(results):
            typer.echo(line)
    except SPARQLTimeoutError as e:
        typer.echo(f"Timeout: {e}", err=True)
        raise typer.Exit(ExitCode.TIMEOUT) from e
    except NetworkError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(ExitCode.NETWORK_ERROR) from e
