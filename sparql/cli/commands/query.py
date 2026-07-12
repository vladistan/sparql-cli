"""Query command for executing SPARQL queries against endpoints."""

import sys
import time

import sentry_sdk
import typer

from sparql._version import __version__
from sparql.cli.output import RDF_FORMAT_ACCEPT_HEADERS, OutputFormat
from sparql.core.client import SPARQLClient, _is_rdf_query
from sparql.core.config import AuthType, load_config, resolve_config
from sparql.core.exceptions import ConfigError, NetworkError
from sparql.core.exceptions import TimeoutError as SPARQLTimeoutError
from sparql.core.exit_codes import ExitCode
from sparql.core.logging import get_logger
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
    if sys.stdout.isatty():
        return OutputFormat.table
    return OutputFormat.tsv


def _get_global_options(
    ctx: typer.Context | None,
) -> tuple[str | None, str | None, str | None]:
    if ctx and ctx.obj:
        return (
            ctx.obj.get("profile"),
            ctx.obj.get("endpoint"),
            ctx.obj.get("graph_filter"),
        )
    return None, None, None


def query(
    ctx: typer.Context,
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
    output_fmt: OutputFormat | None = typer.Option(  # noqa: B008
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

    The global --graph/-G option scopes the query to a single named graph
    via the SPARQL default-graph-uri protocol parameter.
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

    # Merge global options (command-specific takes precedence)
    global_profile, global_endpoint, graph_filter = _get_global_options(ctx)
    profile = profile or global_profile
    endpoint = endpoint or global_endpoint

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

    logger = get_logger("query")

    if verbose:
        typer.echo(f"Endpoint: {resolved.endpoint}", err=True)
        typer.echo(f"Timeout: {resolved.timeout}s", err=True)
        typer.echo("Query:", err=True)
        typer.echo(query_text, err=True)
        typer.echo("---", err=True)

    client = SPARQLClient(
        endpoint_url=resolved.endpoint,
        timeout=resolved.timeout,
        user_agent=resolved.user_agent or f"sparql-tool/{__version__}",
        username=resolved.username,
        password=resolved.password,
        digest_auth=resolved.auth_type == AuthType.DIGEST,
        http_method=resolved.http_method.value,
    )

    # Resolve output format with precedence:
    # --table > --jsonl > --format > TTY detection
    if table:
        output_format = OutputFormat.table
    elif jsonl:
        output_format = OutputFormat.jsonl
    elif output_fmt is not None:
        output_format = output_fmt
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

    logger.debug(
        "query.execute",
        endpoint=resolved.endpoint,
        output_format=output_format.value,
        query_bytes=len(query_text),
    )

    # Validate: RDF formats require CONSTRUCT/DESCRIBE queries
    if (
        output_format in RDF_FORMAT_ACCEPT_HEADERS
        and not _is_rdf_query(query_text)
    ):
        typer.echo(
            f"RDF format '{output_format.value}' requires a CONSTRUCT"
            f" or DESCRIBE query. SELECT/ASK queries return tabular"
            f" data — use table, csv, tsv, json, or sparql11 instead.",
            err=True,
        )
        raise typer.Exit(ExitCode.INPUT_ERROR)

    try:
        start_time = time.perf_counter()
        with sentry_sdk.start_span(op="sparql.query", name=output_format.value):
            # Check if query is CONSTRUCT/DESCRIBE and format is RDF
            if output_format in RDF_FORMAT_ACCEPT_HEADERS and _is_rdf_query(query_text):
                # RDF pass-through: server serializes, we output raw response
                accept_header = RDF_FORMAT_ACCEPT_HEADERS[output_format]
                rdf_response = client.execute_rdf(
                    query_text, accept_header, default_graph_uri=graph_filter
                )
                typer.echo(rdf_response)
            else:
                # Tabular formats for SELECT/ASK queries
                results = client.execute(query_text, default_graph_uri=graph_filter)
                for line in formatter.format(results):
                    typer.echo(line)
        elapsed = time.perf_counter() - start_time
        logger.debug("query.complete", duration_s=round(elapsed, 3))
    except SPARQLTimeoutError as e:
        typer.echo(f"Timeout: {e}", err=True)
        raise typer.Exit(ExitCode.TIMEOUT) from e
    except NetworkError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(ExitCode.NETWORK_ERROR) from e
