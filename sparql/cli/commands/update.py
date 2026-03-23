"""Update command for executing SPARQL UPDATE operations against endpoints."""

import sys

import sentry_sdk
import typer

from sparql._version import __version__
from sparql.core.client import SPARQLClient
from sparql.core.config import AuthType, load_config, resolve_config
from sparql.core.exceptions import ConfigError, NetworkError
from sparql.core.exceptions import TimeoutError as SPARQLTimeoutError
from sparql.core.exit_codes import ExitCode
from sparql.core.logging import get_logger
from sparql.core.query_source import resolve_query_source


def _get_global_options(
    ctx: typer.Context | None,
) -> tuple[str | None, str | None]:
    if ctx and ctx.obj:
        return (
            ctx.obj.get("profile"),
            ctx.obj.get("endpoint"),
        )
    return None, None


def update(
    ctx: typer.Context,
    update_file: str | None = typer.Argument(  # noqa: B008
        None,
        help="SPARQL update file (.ru) or inline update string",
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
        help="Execute inline SPARQL update",
    ),
    timeout: float | None = typer.Option(  # noqa: B008
        None,
        "--timeout",
        "-t",
        help="Update timeout in seconds (overrides config)",
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
    verbose: bool = typer.Option(  # noqa: B008
        False,
        "--verbose",
        help="Show endpoint and update before execution",
    ),
) -> None:
    """Execute a SPARQL UPDATE operation against an endpoint.

    Update can be provided via file, -e inline, or stdin.
    Sends POST with Content-Type: application/sparql-update.
    """
    stdin = None
    if not sys.stdin.isatty():
        stdin = sys.stdin

    try:
        update_text = resolve_query_source(
            inline=execute,
            file_path=update_file,
            stdin=stdin,
        )
    except ConfigError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(ExitCode.INPUT_ERROR) from e

    # Merge global options (command-specific takes precedence)
    global_profile, global_endpoint = _get_global_options(ctx)
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

    logger = get_logger("update")

    if verbose:
        typer.echo(f"Update endpoint: {resolved.update_endpoint}", err=True)
        typer.echo(f"Timeout: {resolved.timeout}s", err=True)
        typer.echo("Update:", err=True)
        typer.echo(update_text, err=True)
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

    logger.debug(
        "update.execute",
        endpoint=resolved.update_endpoint,
        update_bytes=len(update_text),
    )

    try:
        with sentry_sdk.start_span(
            op="sparql.update", name="SPARQL UPDATE"
        ):
            result = client.execute_update(
                update_text, resolved.update_endpoint
            )

        if result.success:
            typer.echo(f"Update successful (HTTP {result.status_code})")
            logger.debug("update.complete", status_code=result.status_code)
        else:
            typer.echo(
                f"Update failed (HTTP {result.status_code}): "
                f"{result.message}",
                err=True,
            )
            raise typer.Exit(ExitCode.NETWORK_ERROR)
    except SPARQLTimeoutError as e:
        typer.echo(f"Timeout: {e}", err=True)
        raise typer.Exit(ExitCode.TIMEOUT) from e
    except NetworkError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(ExitCode.NETWORK_ERROR) from e
