"""SPARQL CLI main entry point and command registration."""

import atexit
from typing import Annotated

import sentry_sdk
import typer

from sparql._version import __version__
from sparql.cli.commands.config import config_app
from sparql.cli.commands.convenience import (
    classes,
    explore,
    graphs,
    object,
    objects,
    predicates,
)
from sparql.cli.commands.query import query
from sparql.core.logging import setup_logging
from sparql.core.monitoring import setup_sentry


class SentryTestError(RuntimeError):
    """Test exception for validating Sentry integration."""


app = typer.Typer(
    help="SPARQL CLI - Query SPARQL endpoints from the command line",
    no_args_is_help=True,
)

# Register config subcommand group
app.add_typer(config_app, name="config")


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"sparql {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            help="Show version and exit",
            callback=version_callback,
            is_eager=True,
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", help="Enable verbose logging"),
    ] = False,
    profile: Annotated[
        str | None,
        typer.Option(
            "--profile",
            "-P",
            help="Use named endpoint profile (global, can also be set per-command)",
        ),
    ] = None,
    endpoint: Annotated[
        str | None,
        typer.Option(
            "--endpoint",
            "-E",
            help="SPARQL endpoint URL (global, can also be set per-command)",
        ),
    ] = None,
    show_graphs: Annotated[
        bool,
        typer.Option(
            "--graphs/--no-graphs",
            "-g",
            help="Show graph column in output",
        ),
    ] = False,
    graph_filter: Annotated[
        str | None,
        typer.Option(
            "--graph",
            "-G",
            help="Filter to specific named graph URI",
        ),
    ] = None,
) -> None:
    """SPARQL CLI - Query SPARQL endpoints from the command line."""
    setup_logging(verbose)
    setup_sentry()

    # Performance monitoring for all CLI operations
    transaction = sentry_sdk.start_transaction(
        op="cli",
        name=ctx.invoked_subcommand or "sparql"
    )
    transaction.__enter__()

    def cleanup() -> None:
        transaction.__exit__(None, None, None)
        sentry_sdk.flush(timeout=2)

    atexit.register(cleanup)

    # Store global options in context for subcommands to access
    ctx.ensure_object(dict)
    ctx.obj["profile"] = profile
    ctx.obj["endpoint"] = endpoint
    ctx.obj["show_graphs"] = show_graphs
    ctx.obj["graph_filter"] = graph_filter


@app.command()
def test_sentry() -> None:
    """Send test events to Sentry for Phase 1 validation.

    This command sends a test exception and performance transaction to verify
    Sentry integration is working correctly. Check your Sentry console to
    confirm events are being received.
    """
    # 1. Error tracking test
    try:
        raise SentryTestError("Phase 1 Sentry test exception")
    except Exception as e:
        sentry_sdk.capture_exception(e)

    # 2. Performance tracing test (parent + child spans)
    with sentry_sdk.start_transaction(op="test", name="phase1_test"):
        with sentry_sdk.start_span(op="parent", description="Parent span"):
            with sentry_sdk.start_span(op="child", description="Child span"):
                pass

    # 3. Flush to ensure delivery
    sentry_sdk.flush(timeout=5)

    # 4. Print verification instructions
    typer.echo("✓ Test events sent to Sentry", err=True)
    typer.echo("", err=True)
    typer.echo("Verify in Sentry console:", err=True)
    typer.echo("  1. Issues → Check for 'Phase 1 Sentry test exception'", err=True)
    typer.echo(
        "  2. Performance → Check for 'phase1_test' transaction"
        " with parent/child spans",
        err=True,
    )


# Register commands
app.command()(query)
app.command()(graphs)
app.command()(classes)
app.command()(predicates)
app.command()(explore)
app.command()(objects)
app.command()(object)
