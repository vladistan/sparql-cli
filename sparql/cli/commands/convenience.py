"""Convenience commands for common SPARQL exploration tasks."""

import sys
import time

import typer

from sparql._version import __version__
from sparql.cli.output import OutputFormat
from sparql.core.client import SPARQLClient
from sparql.core.config import AuthType, load_config, resolve_config
from sparql.core.exceptions import ConfigError, NetworkError
from sparql.core.exceptions import TimeoutError as SPARQLTimeoutError
from sparql.core.exit_codes import ExitCode
from sparql.core.logging import get_logger
from sparql.core.prefixes import PrefixResolver
from sparql.formatters import (
    CSVFormatter,
    Formatter,
    JSONFormatter,
    TableFormatter,
    TSVFormatter,
)


def _detect_default_format() -> OutputFormat:
    if sys.stdout.isatty():
        return OutputFormat.table
    return OutputFormat.tsv


def _get_formatter(
    output_format: OutputFormat,
    prefix_resolver: PrefixResolver | None = None,
) -> Formatter:
    if output_format == OutputFormat.json:
        return JSONFormatter(jsonl=False, prefix_resolver=prefix_resolver)
    if output_format == OutputFormat.jsonl:
        return JSONFormatter(jsonl=True, prefix_resolver=prefix_resolver)
    if output_format == OutputFormat.table:
        return TableFormatter(max_width=60, prefix_resolver=prefix_resolver)
    if output_format == OutputFormat.csv:
        return CSVFormatter(skip_header=False, prefix_resolver=prefix_resolver)
    if output_format == OutputFormat.tsv:
        return TSVFormatter(skip_header=False, prefix_resolver=prefix_resolver)
    # Default to JSON
    return JSONFormatter(jsonl=False, prefix_resolver=prefix_resolver)


def _get_global_options(
    ctx: typer.Context | None,
) -> tuple[str | None, str | None, bool, str | None]:
    if ctx and ctx.obj:
        return (
            ctx.obj.get("profile"),
            ctx.obj.get("endpoint"),
            ctx.obj.get("show_graphs", False),
            ctx.obj.get("graph_filter"),
        )
    return None, None, False, None


def _execute_convenience_query(
    query: str,
    endpoint: str | None,
    profile: str | None,
    timeout: float | None,
    format: OutputFormat | None,
    verbose: bool = False,
    ctx: typer.Context | None = None,
) -> None:
    """Execute a SPARQL query and output formatted results.

    Handles configuration resolution, client creation, execution, and error handling.
    """
    logger = get_logger("convenience")

    # Merge global options (command-specific takes precedence)
    global_profile, global_endpoint, _, _ = _get_global_options(ctx)
    profile = profile or global_profile
    endpoint = endpoint or global_endpoint

    try:
        config = load_config()
        resolved = resolve_config(
            config,
            profile=profile,
            cli_endpoint=endpoint,
            cli_timeout=timeout,
        )
    except ConfigError as e:
        typer.echo(f"Config error: {e}", err=True)
        raise typer.Exit(ExitCode.CONFIG_ERROR) from e

    if verbose:
        typer.echo(f"Endpoint: {resolved.endpoint}", err=True)
        typer.echo(f"Timeout: {resolved.timeout}s", err=True)
        typer.echo("Query:", err=True)
        typer.echo(query, err=True)
        typer.echo("---", err=True)

    logger.debug(
        "endpoint.resolved",
        endpoint=resolved.endpoint,
        timeout=resolved.timeout,
    )

    client = SPARQLClient(
        endpoint_url=resolved.endpoint,
        timeout=resolved.timeout,
        user_agent=resolved.user_agent or f"sparql-tool/{__version__}",
        username=resolved.username,
        password=resolved.password,
        digest_auth=resolved.auth_type == AuthType.DIGEST,
    )

    output_format = format if format is not None else _detect_default_format()

    # Create prefix resolver if prefixes configured
    prefix_resolver = PrefixResolver(config.prefixes) if config.prefixes else None
    formatter = _get_formatter(output_format, prefix_resolver)

    logger.debug("query.execute", query=query, query_bytes=len(query))

    try:
        start_time = time.perf_counter()
        results = client.execute(query)
        result_count = 0
        for line in formatter.format(results):
            typer.echo(line)
            result_count += 1
        elapsed = time.perf_counter() - start_time
        logger.debug(
            "query.complete", duration_s=round(elapsed, 3), results=result_count
        )
    except SPARQLTimeoutError as e:
        typer.echo(f"Timeout: {e}", err=True)
        raise typer.Exit(ExitCode.TIMEOUT) from e
    except NetworkError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(ExitCode.NETWORK_ERROR) from e


def graphs(
    ctx: typer.Context,
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
    limit: int = typer.Option(  # noqa: B008
        100,
        "--limit",
        "-n",
        help="Maximum number of results (default: 100)",
    ),
    timeout: float | None = typer.Option(  # noqa: B008
        None,
        "--timeout",
        "-t",
        help="Query timeout in seconds",
    ),
    format: OutputFormat | None = typer.Option(  # noqa: B008
        None,
        "--format",
        "-f",
        help="Output format (default: table for TTY, tsv for pipes)",
    ),
    verbose: bool = typer.Option(  # noqa: B008
        False,
        "--verbose",
        "-v",
        help="Show endpoint and query before execution",
    ),
) -> None:
    """List named graphs in the endpoint.

    Shows all distinct named graphs that contain data.
    """
    query = (
        "SELECT DISTINCT ?graph WHERE { GRAPH ?graph { ?s ?p ?o } } "
        f"LIMIT {limit}"
    )
    _execute_convenience_query(query, endpoint, profile, timeout, format, verbose, ctx)


def classes(
    ctx: typer.Context,
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
    limit: int = typer.Option(  # noqa: B008
        100,
        "--limit",
        "-n",
        help="Maximum number of results (default: 100)",
    ),
    timeout: float | None = typer.Option(  # noqa: B008
        None,
        "--timeout",
        "-t",
        help="Query timeout in seconds",
    ),
    format: OutputFormat | None = typer.Option(  # noqa: B008
        None,
        "--format",
        "-f",
        help="Output format (default: table for TTY, tsv for pipes)",
    ),
    labels: bool = typer.Option(  # noqa: B008
        False,
        "--labels/--no-labels",
        "-l",
        help="Include rdfs:label for each class (slower, not all endpoints)",
    ),
    show_graphs: bool = typer.Option(  # noqa: B008
        False,
        "--graphs/--no-graphs",
        "-g",
        help="Show graph column in output",
    ),
    graph_filter: str | None = typer.Option(  # noqa: B008
        None,
        "--graph",
        "-G",
        help="Filter to specific named graph URI",
    ),
    verbose: bool = typer.Option(  # noqa: B008
        False,
        "--verbose",
        "-v",
        help="Show endpoint and query before execution",
    ),
) -> None:
    """List distinct RDF classes from endpoint.

    Use --labels to also fetch rdfs:label for each class (if available).
    Use -g to show which graph each class comes from.
    Use -G <uri> to query only that named graph.
    """
    # Merge global graph options (command-specific takes precedence)
    _, _, global_show_graphs, global_graph_filter = _get_global_options(ctx)
    show_graph = show_graphs or global_show_graphs
    graph_uri = graph_filter or global_graph_filter

    if labels:
        # Use subquery: first find classes (limited), then lookup labels only for those
        # Include PREFIX declaration for endpoints that require it (e.g., MarkLogic)
        if show_graph:
            query = f"""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?graph ?class ?label WHERE {{
  {{
    SELECT DISTINCT ?graph ?class
    WHERE {{ GRAPH ?graph {{ ?s a ?class }} }} LIMIT {limit}
  }}
  OPTIONAL {{
    ?class rdfs:label ?label .
    FILTER(LANG(?label) = "en" || LANG(?label) = "")
  }}
}}"""
        elif graph_uri:
            query = f"""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?class ?label WHERE {{
  {{
    SELECT DISTINCT ?class
    WHERE {{ GRAPH <{graph_uri}> {{ ?s a ?class }} }} LIMIT {limit}
  }}
  OPTIONAL {{
    ?class rdfs:label ?label .
    FILTER(LANG(?label) = "en" || LANG(?label) = "")
  }}
}}"""
        else:
            query = f"""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?class ?label WHERE {{
  {{
    SELECT DISTINCT ?class WHERE {{ ?s a ?class }} LIMIT {limit}
  }}
  OPTIONAL {{
    ?class rdfs:label ?label .
    FILTER(LANG(?label) = "en" || LANG(?label) = "")
  }}
}}"""
    else:
        if show_graph:
            query = (
                "SELECT DISTINCT ?graph ?class "
                f"WHERE {{ GRAPH ?graph {{ ?s a ?class }} }} LIMIT {limit}"
            )
        elif graph_uri:
            query = (
                "SELECT DISTINCT ?class "
                f"WHERE {{ GRAPH <{graph_uri}> {{ ?s a ?class }} }} LIMIT {limit}"
            )
        else:
            query = f"SELECT DISTINCT ?class WHERE {{ ?s a ?class }} LIMIT {limit}"
    _execute_convenience_query(query, endpoint, profile, timeout, format, verbose, ctx)


def predicates(
    ctx: typer.Context,
    predicate_uri: str | None = typer.Argument(  # noqa: B008
        None,
        help="Optional predicate URI to show values for (e.g., rdf:type)",
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
    limit: int = typer.Option(  # noqa: B008
        100,
        "--limit",
        "-n",
        help="Maximum number of results (default: 100)",
    ),
    timeout: float | None = typer.Option(  # noqa: B008
        None,
        "--timeout",
        "-t",
        help="Query timeout in seconds",
    ),
    format: OutputFormat | None = typer.Option(  # noqa: B008
        None,
        "--format",
        "-f",
        help="Output format (default: table for TTY, tsv for pipes)",
    ),
    labels: bool = typer.Option(  # noqa: B008
        False,
        "--labels/--no-labels",
        "-l",
        help="Include rdfs:label (slower, not all endpoints)",
    ),
    values_only: bool = typer.Option(  # noqa: B008
        False,
        "--values/--subjects",
        help="Show only distinct values (objects), not subjects",
    ),
    show_graphs: bool = typer.Option(  # noqa: B008
        False,
        "--graphs/--no-graphs",
        "-g",
        help="Show graph column in output",
    ),
    graph_filter: str | None = typer.Option(  # noqa: B008
        None,
        "--graph",
        "-G",
        help="Filter to specific named graph URI",
    ),
    verbose: bool = typer.Option(  # noqa: B008
        False,
        "--verbose",
        "-v",
        help="Show endpoint and query before execution",
    ),
) -> None:
    """List predicates, or show usage of a specific predicate.

    Without argument: lists all distinct predicates in the endpoint.
    With PREDICATE_URI: shows subject-value pairs using that predicate.

    Examples:
      sparql predicates              # list all predicates
      sparql predicates rdf:type     # show who has rdf:type and what values
      sparql predicates rdf:type --values  # show only distinct values
    """
    # Merge global graph options (command-specific takes precedence)
    _, _, global_show_graphs, global_graph_filter = _get_global_options(ctx)
    show_graph = show_graphs or global_show_graphs
    graph_uri = graph_filter or global_graph_filter

    # Expand prefixed predicate URI if provided
    config = load_config()
    if predicate_uri and config.prefixes:
        resolver = PrefixResolver(config.prefixes)
        predicate_uri = resolver.expand(predicate_uri)

    if predicate_uri:
        # Show usage of specific predicate
        query = _build_predicate_usage_query(
            predicate_uri, limit, labels, values_only, show_graph, graph_uri
        )
    else:
        # List all predicates
        query = _build_predicate_list_query(limit, labels, show_graph, graph_uri)

    _execute_convenience_query(query, endpoint, profile, timeout, format, verbose, ctx)


def _build_predicate_list_query(
    limit: int, labels: bool, show_graph: bool, graph_uri: str | None
) -> str:
    if labels:
        if show_graph:
            return f"""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?graph ?predicate ?label WHERE {{
  {{
    SELECT DISTINCT ?graph ?predicate
    WHERE {{ GRAPH ?graph {{ ?s ?predicate ?o }} }} LIMIT {limit}
  }}
  OPTIONAL {{
    ?predicate rdfs:label ?label .
    FILTER(LANG(?label) = "en" || LANG(?label) = "")
  }}
}}"""
        elif graph_uri:
            return f"""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?predicate ?label WHERE {{
  {{
    SELECT DISTINCT ?predicate
    WHERE {{ GRAPH <{graph_uri}> {{ ?s ?predicate ?o }} }} LIMIT {limit}
  }}
  OPTIONAL {{
    ?predicate rdfs:label ?label .
    FILTER(LANG(?label) = "en" || LANG(?label) = "")
  }}
}}"""
        else:
            return f"""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?predicate ?label WHERE {{
  {{
    SELECT DISTINCT ?predicate WHERE {{ ?s ?predicate ?o }} LIMIT {limit}
  }}
  OPTIONAL {{
    ?predicate rdfs:label ?label .
    FILTER(LANG(?label) = "en" || LANG(?label) = "")
  }}
}}"""
    else:
        if show_graph:
            return (
                "SELECT DISTINCT ?graph ?predicate "
                f"WHERE {{ GRAPH ?graph {{ ?s ?predicate ?o }} }} LIMIT {limit}"
            )
        elif graph_uri:
            return (
                "SELECT DISTINCT ?predicate "
                f"WHERE {{ GRAPH <{graph_uri}> {{ ?s ?predicate ?o }} }} LIMIT {limit}"
            )
        else:
            return (
                "SELECT DISTINCT ?predicate "
                f"WHERE {{ ?s ?predicate ?o }} LIMIT {limit}"
            )


def _build_predicate_usage_query(
    predicate_uri: str,
    limit: int,
    labels: bool,
    values_only: bool,
    show_graph: bool,
    graph_uri: str | None,
) -> str:
    if values_only:
        # Show only distinct values (objects)
        if labels:
            if show_graph:
                return f"""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?graph ?value ?label WHERE {{
  {{
    SELECT DISTINCT ?graph ?value
    WHERE {{ GRAPH ?graph {{ ?s <{predicate_uri}> ?value }} }} LIMIT {limit}
  }}
  OPTIONAL {{
    ?value rdfs:label ?label .
    FILTER(LANG(?label) = "en" || LANG(?label) = "")
  }}
}}"""
            elif graph_uri:
                return f"""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?value ?label WHERE {{
  {{
    SELECT DISTINCT ?value
    WHERE {{ GRAPH <{graph_uri}> {{ ?s <{predicate_uri}> ?value }} }} LIMIT {limit}
  }}
  OPTIONAL {{
    ?value rdfs:label ?label .
    FILTER(LANG(?label) = "en" || LANG(?label) = "")
  }}
}}"""
            else:
                return f"""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?value ?label WHERE {{
  {{
    SELECT DISTINCT ?value
    WHERE {{ ?s <{predicate_uri}> ?value }} LIMIT {limit}
  }}
  OPTIONAL {{
    ?value rdfs:label ?label .
    FILTER(LANG(?label) = "en" || LANG(?label) = "")
  }}
}}"""
        else:
            if show_graph:
                return (
                    "SELECT DISTINCT ?graph ?value "
                    f"WHERE {{ GRAPH ?graph {{ ?s <{predicate_uri}> ?value }} }} "
                    f"LIMIT {limit}"
                )
            elif graph_uri:
                return (
                    "SELECT DISTINCT ?value "
                    f"WHERE {{ GRAPH <{graph_uri}> {{ ?s <{predicate_uri}> ?value }} }}"
                    f" LIMIT {limit}"
                )
            else:
                return (
                    "SELECT DISTINCT ?value "
                    f"WHERE {{ ?s <{predicate_uri}> ?value }} LIMIT {limit}"
                )
    else:
        # Show subject-value pairs
        if show_graph:
            return (
                "SELECT DISTINCT ?graph ?subject ?value "
                f"WHERE {{ GRAPH ?graph {{ ?subject <{predicate_uri}> ?value }} }} "
                f"LIMIT {limit}"
            )
        elif graph_uri:
            return (
                "SELECT DISTINCT ?subject ?value WHERE "
                f"{{ GRAPH <{graph_uri}> {{ ?subject <{predicate_uri}> ?value }} }}"
                f" LIMIT {limit}"
            )
        else:
            return (
                "SELECT DISTINCT ?subject ?value "
                f"WHERE {{ ?subject <{predicate_uri}> ?value }} LIMIT {limit}"
            )


def explore(
    ctx: typer.Context,
    uri: str = typer.Argument(  # noqa: B008
        ...,
        help="URI to explore (finds all triples where this URI appears)",
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
    limit: int = typer.Option(  # noqa: B008
        100,
        "--limit",
        "-n",
        help="Maximum number of results (default: 100)",
    ),
    timeout: float | None = typer.Option(  # noqa: B008
        None,
        "--timeout",
        "-t",
        help="Query timeout in seconds",
    ),
    format: OutputFormat | None = typer.Option(  # noqa: B008
        None,
        "--format",
        "-f",
        help="Output format (default: table for TTY, tsv for pipes)",
    ),
    show_graphs: bool = typer.Option(  # noqa: B008
        False,
        "--graphs/--no-graphs",
        "-g",
        help="Show graph column in output",
    ),
    graph_filter: str | None = typer.Option(  # noqa: B008
        None,
        "--graph",
        "-G",
        help="Filter to specific named graph URI",
    ),
    verbose: bool = typer.Option(  # noqa: B008
        False,
        "--verbose",
        "-v",
        help="Show endpoint and query before execution",
    ),
) -> None:
    """Explore triples where URI appears as subject, predicate, or object.

    Finds all relationships involving the specified URI in any position.

    URI can be a full URI or prefixed name (e.g., dbo:Person, wd:Q42).
    Use -g to show which graph each triple comes from.
    Use -G <uri> to query only that named graph.
    """
    # Merge global graph options (command-specific takes precedence)
    _, _, global_show_graphs, global_graph_filter = _get_global_options(ctx)
    show_graph = show_graphs or global_show_graphs
    graph_uri = graph_filter or global_graph_filter

    # Expand prefixed names to full URIs
    config = load_config()
    if config.prefixes:
        resolver = PrefixResolver(config.prefixes)
        uri = resolver.expand(uri)

    if show_graph:
        query = f"""SELECT ?graph ?s ?p ?o WHERE {{
  GRAPH ?graph {{
    {{ <{uri}> ?p ?o . BIND(<{uri}> AS ?s) }}
    UNION
    {{ ?s <{uri}> ?o . BIND(<{uri}> AS ?p) }}
    UNION
    {{ ?s ?p <{uri}> . BIND(<{uri}> AS ?o) }}
  }}
}} LIMIT {limit}"""
    elif graph_uri:
        query = f"""SELECT ?s ?p ?o WHERE {{
  GRAPH <{graph_uri}> {{
    {{ <{uri}> ?p ?o . BIND(<{uri}> AS ?s) }}
    UNION
    {{ ?s <{uri}> ?o . BIND(<{uri}> AS ?p) }}
    UNION
    {{ ?s ?p <{uri}> . BIND(<{uri}> AS ?o) }}
  }}
}} LIMIT {limit}"""
    else:
        query = f"""SELECT ?s ?p ?o WHERE {{
  {{ <{uri}> ?p ?o . BIND(<{uri}> AS ?s) }}
  UNION
  {{ ?s <{uri}> ?o . BIND(<{uri}> AS ?p) }}
  UNION
  {{ ?s ?p <{uri}> . BIND(<{uri}> AS ?o) }}
}} LIMIT {limit}"""
    _execute_convenience_query(query, endpoint, profile, timeout, format, verbose, ctx)


def objects(
    ctx: typer.Context,
    class_uri: str = typer.Argument(  # noqa: B008
        ...,
        help="Class URI to list instances of (e.g., dbo:Person, foaf:Agent)",
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
    limit: int = typer.Option(  # noqa: B008
        100,
        "--limit",
        "-n",
        help="Maximum number of results (default: 100)",
    ),
    timeout: float | None = typer.Option(  # noqa: B008
        None,
        "--timeout",
        "-t",
        help="Query timeout in seconds",
    ),
    format: OutputFormat | None = typer.Option(  # noqa: B008
        None,
        "--format",
        "-f",
        help="Output format (default: table for TTY, tsv for pipes)",
    ),
    labels: bool = typer.Option(  # noqa: B008
        False,
        "--labels/--no-labels",
        "-l",
        help="Include rdfs:label for each object (slower, not all endpoints)",
    ),
    show_graphs: bool = typer.Option(  # noqa: B008
        False,
        "--graphs/--no-graphs",
        "-g",
        help="Show graph column in output",
    ),
    graph_filter: str | None = typer.Option(  # noqa: B008
        None,
        "--graph",
        "-G",
        help="Filter to specific named graph URI",
    ),
    verbose: bool = typer.Option(  # noqa: B008
        False,
        "--verbose",
        "-v",
        help="Show endpoint and query before execution",
    ),
) -> None:
    """List instances (objects) of a given RDF class.

    CLASS_URI can be a full URI or prefixed name (e.g., dbo:Person, foaf:Agent).

    Use --labels to also fetch rdfs:label for each instance (if available).
    Use -g to show which graph each instance comes from.
    Use -G <uri> to query only that named graph.
    """
    # Merge global graph options (command-specific takes precedence)
    _, _, global_show_graphs, global_graph_filter = _get_global_options(ctx)
    show_graph = show_graphs or global_show_graphs
    graph_uri = graph_filter or global_graph_filter

    # Expand prefixed names to full URIs
    config = load_config()
    if config.prefixes:
        resolver = PrefixResolver(config.prefixes)
        class_uri = resolver.expand(class_uri)

    if labels:
        if show_graph:
            query = f"""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?graph ?object ?label WHERE {{
  {{
    SELECT DISTINCT ?graph ?object
    WHERE {{ GRAPH ?graph {{ ?object a <{class_uri}> }} }} LIMIT {limit}
  }}
  OPTIONAL {{
    ?object rdfs:label ?label .
    FILTER(LANG(?label) = "en" || LANG(?label) = "")
  }}
}}"""
        elif graph_uri:
            query = f"""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?object ?label WHERE {{
  {{
    SELECT DISTINCT ?object
    WHERE {{ GRAPH <{graph_uri}> {{ ?object a <{class_uri}> }} }} LIMIT {limit}
  }}
  OPTIONAL {{
    ?object rdfs:label ?label .
    FILTER(LANG(?label) = "en" || LANG(?label) = "")
  }}
}}"""
        else:
            query = f"""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?object ?label WHERE {{
  {{
    SELECT DISTINCT ?object WHERE {{ ?object a <{class_uri}> }} LIMIT {limit}
  }}
  OPTIONAL {{
    ?object rdfs:label ?label .
    FILTER(LANG(?label) = "en" || LANG(?label) = "")
  }}
}}"""
    else:
        if show_graph:
            query = (
                "SELECT DISTINCT ?graph ?object "
                f"WHERE {{ GRAPH ?graph {{ ?object a <{class_uri}> }} }} LIMIT {limit}"
            )
        elif graph_uri:
            query = (
                "SELECT DISTINCT ?object "
                f"WHERE {{ GRAPH <{graph_uri}> {{ ?object a <{class_uri}> }} }} "
                f"LIMIT {limit}"
            )
        else:
            query = (
                "SELECT DISTINCT ?object "
                f"WHERE {{ ?object a <{class_uri}> }} LIMIT {limit}"
            )
    _execute_convenience_query(query, endpoint, profile, timeout, format, verbose, ctx)


def object(
    ctx: typer.Context,
    uri: str = typer.Argument(  # noqa: B008
        ...,
        help="Instance URI to describe (e.g., dbr:Berlin, wd:Q42)",
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
    limit: int = typer.Option(  # noqa: B008
        100,
        "--limit",
        "-n",
        help="Maximum number of results (default: 100)",
    ),
    timeout: float | None = typer.Option(  # noqa: B008
        None,
        "--timeout",
        "-t",
        help="Query timeout in seconds",
    ),
    format: OutputFormat | None = typer.Option(  # noqa: B008
        None,
        "--format",
        "-f",
        help="Output format (default: table for TTY, tsv for pipes)",
    ),
    show_graphs: bool = typer.Option(  # noqa: B008
        False,
        "--graphs/--no-graphs",
        "-g",
        help="Show graph column in output",
    ),
    graph_filter: str | None = typer.Option(  # noqa: B008
        None,
        "--graph",
        "-G",
        help="Filter to specific named graph URI",
    ),
    verbose: bool = typer.Option(  # noqa: B008
        False,
        "--verbose",
        "-v",
        help="Show endpoint and query before execution",
    ),
) -> None:
    """Show all predicates and values for a specific instance.

    URI can be a full URI or prefixed name (e.g., dbr:Berlin, wd:Q42).

    Returns all properties (predicate-value pairs) of the given resource.
    Use -g to see which named graph each triple comes from.
    Use -G <uri> to query only that named graph.
    """
    # Merge global graph options (command-specific takes precedence)
    _, _, global_show_graphs, global_graph_filter = _get_global_options(ctx)
    show_graph = show_graphs or global_show_graphs
    graph_uri = graph_filter or global_graph_filter

    # Expand prefixed names to full URIs
    config = load_config()
    if config.prefixes:
        resolver = PrefixResolver(config.prefixes)
        uri = resolver.expand(uri)

    if show_graph:
        query = f"""SELECT DISTINCT ?graph ?predicate ?value WHERE {{
  GRAPH ?graph {{ <{uri}> ?predicate ?value }}
}} LIMIT {limit}"""
    elif graph_uri:
        query = f"""SELECT DISTINCT ?predicate ?value WHERE {{
  GRAPH <{graph_uri}> {{ <{uri}> ?predicate ?value }}
}} LIMIT {limit}"""
    else:
        query = (
            "SELECT DISTINCT ?predicate ?value "
            f"WHERE {{ <{uri}> ?predicate ?value }} LIMIT {limit}"
        )
    _execute_convenience_query(query, endpoint, profile, timeout, format, verbose, ctx)
