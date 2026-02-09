"""Configuration models and loading for SPARQL CLI."""

import os
import tomllib
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from sparql.core.exceptions import ConfigError
from sparql.core.prefixes import STANDARD_PREFIXES


class AuthType(str, Enum):
    """Authentication methods supported for SPARQL endpoints."""

    NONE = "none"
    BASIC = "basic"
    DIGEST = "digest"


class EndpointType(str, Enum):
    """SPARQL endpoint server type for server-specific handling."""

    GENERIC = "generic"
    MARKLOGIC = "marklogic"
    BLAZEGRAPH = "blazegraph"
    STARDOG = "stardog"
    FUSEKI = "fuseki"
    VIRTUOSO = "virtuoso"
    GRAPHDB = "graphdb"


class HTTPMethod(str, Enum):
    """HTTP methods for SPARQL queries."""

    GET = "GET"
    POST = "POST"


class EndpointProfile(BaseModel):
    """Named endpoint configuration with optional authentication."""

    url: str
    endpoint_type: EndpointType = EndpointType.GENERIC
    timeout: float | None = None
    user_agent: str | None = None
    username: str | None = None
    password: str | None = None
    auth_type: AuthType = AuthType.NONE
    http_method: HTTPMethod | None = None
    update_url: str | None = None

    # Server-specific parameters
    database: str | None = None  # MarkLogic database name
    namespace: str | None = None  # Blazegraph namespace
    repository: str | None = None  # GraphDB repository
    reasoning: bool | None = None  # Stardog reasoning enabled

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError(f"Invalid URL: {v} (must start with http:// or https://)")
        return v


class AppConfig(BaseModel):
    """Application configuration with defaults and endpoint profiles."""

    default_endpoint: str = Field(default="wikidata")
    default_timeout: float = Field(default=30.0)
    default_format: str = Field(default="json")
    endpoints: dict[str, EndpointProfile] = Field(default_factory=lambda: {
        "wikidata": EndpointProfile(
            url="https://query.wikidata.org/sparql",
            timeout=60.0,
        ),
        "dbpedia": EndpointProfile(
            url="https://dbpedia.org/sparql",
            endpoint_type=EndpointType.VIRTUOSO,
            timeout=30.0,
        ),
        "uniprot": EndpointProfile(
            url="https://sparql.uniprot.org/sparql",
            timeout=60.0,
        ),
    })
    prefixes: dict[str, str] = Field(default_factory=lambda: STANDARD_PREFIXES.copy())


def load_config(config_path: Path | None = None) -> AppConfig:
    """Load configuration from file with fallback path support.

    Search order:
    1. Explicit path (if provided)
    2. ~/.config/sparql/config.toml (XDG standard)
    3. ~/.sparqlrc (legacy)
    4. Default config (no file)
    """
    if config_path is not None:
        return _load_config_file(config_path)

    # Search default locations
    home = Path.home()
    search_paths = [
        home / ".config" / "sparql" / "config.toml",
        home / ".sparqlrc",
    ]

    for path in search_paths:
        if path.exists():
            return _load_config_file(path)

    # No config file found - return defaults
    return AppConfig()


def _load_config_file(path: Path) -> AppConfig:
    """Load and parse a TOML configuration file into AppConfig."""
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"Invalid TOML in {path}: {e}") from e

    # Convert nested endpoint dicts to EndpointProfile objects
    if "endpoints" in data:
        data["endpoints"] = {
            name: EndpointProfile(**profile_data)
            for name, profile_data in data["endpoints"].items()
        }

    # Merge user prefixes with standard prefixes (user overrides standard)
    if "prefixes" in data:
        merged_prefixes = STANDARD_PREFIXES.copy()
        merged_prefixes.update(data["prefixes"])
        data["prefixes"] = merged_prefixes

    return AppConfig(**data)


class ResolvedConfig(BaseModel):
    """Resolved configuration after applying precedence rules.

    Precedence (highest to lowest):
    1. CLI flags
    2. Environment variables
    3. Named profile
    4. Default profile from config
    5. Built-in defaults
    """

    endpoint: str
    endpoint_type: EndpointType = EndpointType.GENERIC
    timeout: float
    format: str
    username: str | None = None
    password: str | None = None
    auth_type: AuthType = AuthType.NONE
    user_agent: str | None = None
    http_method: HTTPMethod = HTTPMethod.POST

    update_endpoint: str = ""

    # Server-specific parameters
    database: str | None = None
    namespace: str | None = None
    repository: str | None = None
    reasoning: bool | None = None


def _derive_update_url(endpoint_url: str, explicit_update_url: str | None) -> str:
    """Derive SPARQL UPDATE endpoint URL.

    Priority: explicit update_url > replace /query path segment > endpoint as-is.
    Only replaces /query in the URL path, not in the hostname.
    """
    if explicit_update_url:
        return explicit_update_url

    # Split at ://  to isolate scheme from rest, then find path
    scheme_sep = endpoint_url.find("://")
    if scheme_sep == -1:
        return endpoint_url
    after_scheme = endpoint_url[scheme_sep + 3 :]
    slash_pos = after_scheme.find("/")
    if slash_pos == -1:
        return endpoint_url

    host = endpoint_url[: scheme_sep + 3 + slash_pos]
    path = after_scheme[slash_pos:]

    if "/query" in path:
        return host + path.replace("/query", "/update", 1)
    return endpoint_url


def resolve_config(
    config: AppConfig,
    *,
    profile: str | None = None,
    cli_endpoint: str | None = None,
    cli_timeout: float | None = None,
    cli_format: str | None = None,
    cli_username: str | None = None,
    cli_password: str | None = None,
    cli_auth_type: AuthType | None = None,
) -> ResolvedConfig:
    """Resolve configuration from all sources with precedence.

    Precedence (highest to lowest):
    1. CLI flags
    2. Environment variables (SPARQL_PROFILE, SPARQL_ENDPOINT, etc.)
    3. Named profile (if --profile specified)
    4. Default profile from config file
    5. Built-in defaults
    """
    # Determine which profile to use
    effective_profile = (
        profile or os.getenv("SPARQL_PROFILE") or config.default_endpoint
    )

    # Look up the profile
    if effective_profile not in config.endpoints:
        available = ", ".join(config.endpoints.keys()) if config.endpoints else "none"
        raise ConfigError(
            f"Unknown endpoint '{effective_profile}'. Available: {available}"
        )

    profile_config = config.endpoints[effective_profile]

    # Resolve endpoint URL: CLI > Env > Profile
    endpoint = (
        cli_endpoint
        or os.getenv("SPARQL_ENDPOINT")
        or profile_config.url
    )

    # Resolve timeout: CLI > Env > Profile > Config default
    env_timeout = os.getenv("SPARQL_TIMEOUT")
    if cli_timeout is not None:
        timeout = cli_timeout
    elif env_timeout:
        timeout = float(env_timeout)
    elif profile_config.timeout is not None:
        timeout = profile_config.timeout
    else:
        timeout = config.default_timeout

    # Resolve auth: CLI > Env > Profile
    username = (
        cli_username
        or os.getenv("SPARQL_USER")
        or profile_config.username
    )
    password = (
        cli_password
        or os.getenv("SPARQL_PASSWORD")
        or profile_config.password
    )

    # Auth type: CLI > Profile (env can set user/pass but not type)
    auth_type = cli_auth_type or profile_config.auth_type

    # Resolve format: CLI > Config default
    format_value = cli_format or config.default_format

    # Resolve HTTP method: Profile > Auto-detect from endpoint type
    # VIRTUOSO endpoints require GET, all others default to POST
    if profile_config.http_method is not None:
        http_method = profile_config.http_method
    elif profile_config.endpoint_type == EndpointType.VIRTUOSO:
        http_method = HTTPMethod.GET
    else:
        http_method = HTTPMethod.POST

    # Derive update endpoint URL
    update_endpoint = _derive_update_url(endpoint, profile_config.update_url)

    return ResolvedConfig(
        endpoint=endpoint,
        endpoint_type=profile_config.endpoint_type,
        timeout=timeout,
        format=format_value,
        username=username,
        password=password,
        auth_type=auth_type,
        user_agent=profile_config.user_agent,
        http_method=http_method,
        update_endpoint=update_endpoint,
        database=profile_config.database,
        namespace=profile_config.namespace,
        repository=profile_config.repository,
        reasoning=profile_config.reasoning,
    )
