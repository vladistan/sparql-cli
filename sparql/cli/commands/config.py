"""Config command for displaying and managing configuration."""

import json
import os

import typer

from sparql.core.config import AuthType, load_config, resolve_config
from sparql.core.exceptions import ConfigError
from sparql.core.exit_codes import ExitCode

config_app = typer.Typer(help="Configuration management commands")

# Width of separator line in human-readable output
SEPARATOR_WIDTH = 40


@config_app.command("show")
def show(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output as JSON",
    ),
) -> None:
    """Display current effective configuration with source attribution."""
    try:
        config = load_config()
        resolved = resolve_config(config)
    except ConfigError as e:
        typer.echo(f"Config error: {e}", err=True)
        raise typer.Exit(ExitCode.CONFIG_ERROR) from e

    # Determine sources for each setting
    env_endpoint = os.getenv("SPARQL_ENDPOINT")
    env_timeout = os.getenv("SPARQL_TIMEOUT")
    env_profile = os.getenv("SPARQL_PROFILE")
    env_user = os.getenv("SPARQL_USER")

    if json_output:
        output = {
            "default_endpoint": config.default_endpoint,
            "effective": {
                "endpoint": resolved.endpoint,
                "endpoint_type": resolved.endpoint_type.value,
                "timeout": resolved.timeout,
                "format": resolved.format,
                "auth_type": resolved.auth_type.value,
                "username": resolved.username,
                "has_password": resolved.password is not None,
                "database": resolved.database,
                "namespace": resolved.namespace,
                "repository": resolved.repository,
                "reasoning": resolved.reasoning,
            },
            "profiles": {
                name: {
                    "url": profile.url,
                    "endpoint_type": profile.endpoint_type.value,
                    "timeout": profile.timeout,
                    "auth_type": profile.auth_type.value,
                    "username": profile.username,
                    "has_password": profile.password is not None,
                    "database": profile.database,
                    "namespace": profile.namespace,
                    "repository": profile.repository,
                    "reasoning": profile.reasoning,
                }
                for name, profile in config.endpoints.items()
            },
        }
        typer.echo(json.dumps(output, indent=2))
    else:
        typer.echo("Current Configuration")
        typer.echo("=" * SEPARATOR_WIDTH)
        typer.echo("")
        typer.echo(f"Default profile: {config.default_endpoint}")
        if env_profile:
            typer.echo(f"  (override: SPARQL_PROFILE={env_profile})")
        typer.echo("")
        typer.echo("Effective Settings:")
        typer.echo(f"  endpoint:  {resolved.endpoint}")
        if env_endpoint:
            typer.echo("    (override: SPARQL_ENDPOINT)")
        typer.echo(f"  type:      {resolved.endpoint_type.value}")
        typer.echo(f"  timeout:   {resolved.timeout}s")
        if env_timeout:
            typer.echo("    (override: SPARQL_TIMEOUT)")
        typer.echo(f"  format:    {resolved.format}")
        if resolved.auth_type != AuthType.NONE:
            typer.echo(f"  auth:      {resolved.auth_type.value}")
            typer.echo(f"  username:  {resolved.username or '(not set)'}")
            if env_user:
                typer.echo("    (override: SPARQL_USER)")
            typer.echo(f"  password:  {'***' if resolved.password else '(not set)'}")
        # Show server-specific params if set
        if resolved.database:
            typer.echo(f"  database:  {resolved.database}")
        if resolved.namespace:
            typer.echo(f"  namespace: {resolved.namespace}")
        if resolved.repository:
            typer.echo(f"  repository: {resolved.repository}")
        if resolved.reasoning is not None:
            typer.echo(f"  reasoning: {resolved.reasoning}")
        typer.echo("")

        if config.endpoints:
            typer.echo("Configured Profiles:")
            for name, profile in config.endpoints.items():
                marker = " *" if name == config.default_endpoint else ""
                typer.echo(f"  [{name}]{marker}")
                typer.echo(f"    url: {profile.url}")
                typer.echo(f"    type: {profile.endpoint_type.value}")
                if profile.timeout:
                    typer.echo(f"    timeout: {profile.timeout}s")
                if profile.auth_type != AuthType.NONE:
                    typer.echo(f"    auth: {profile.auth_type.value}")
                    if profile.username:
                        typer.echo(f"    user: {profile.username}")
                # Server-specific params
                if profile.database:
                    typer.echo(f"    database: {profile.database}")
                if profile.namespace:
                    typer.echo(f"    namespace: {profile.namespace}")
                if profile.repository:
                    typer.echo(f"    repository: {profile.repository}")
                if profile.reasoning is not None:
                    typer.echo(f"    reasoning: {profile.reasoning}")
        else:
            typer.echo("Profiles: none configured")


@config_app.command("profiles")
def profiles() -> None:
    """List available endpoint profiles. Default profile is marked with *."""
    try:
        config = load_config()
    except ConfigError as e:
        typer.echo(f"Config error: {e}", err=True)
        raise typer.Exit(ExitCode.CONFIG_ERROR) from e
    for name in config.endpoints:
        marker = " *" if name == config.default_endpoint else ""
        typer.echo(f"{name}{marker}")
