import pytest

from sparql.core.config import (
    AppConfig,
    AuthType,
    EndpointProfile,
    EndpointType,
    load_config,
    resolve_config,
)
from sparql.core.exceptions import ConfigError

# --- EndpointProfile Tests ---


def test_endpoint_profile_creates_with_url_only():
    profile = EndpointProfile(url="https://query.wikidata.org/sparql")
    assert profile.url == "https://query.wikidata.org/sparql"
    assert profile.timeout is None
    assert profile.username is None
    assert profile.password is None
    assert profile.auth_type == AuthType.NONE


def test_endpoint_profile_creates_with_all_fields():
    profile = EndpointProfile(
        url="https://dbpedia.org/sparql",
        timeout=60.0,
        user_agent="custom-agent/1.0",
        username="admin",
        password="secret",  # pragma: allowlist secret
        auth_type=AuthType.BASIC,
    )
    assert profile.url == "https://dbpedia.org/sparql"
    assert profile.timeout == 60.0
    assert profile.username == "admin"
    assert profile.password == "secret"
    assert profile.auth_type == AuthType.BASIC


def test_endpoint_profile_validates_url_requires_scheme():
    with pytest.raises(ValueError, match="Invalid URL"):
        EndpointProfile(url="query.wikidata.org/sparql")


def test_endpoint_profile_accepts_http_and_https():
    http_profile = EndpointProfile(url="http://localhost:9999/sparql")
    https_profile = EndpointProfile(url="https://example.com/sparql")
    assert http_profile.url.startswith("http://")
    assert https_profile.url.startswith("https://")


def test_auth_type_enum_values():
    assert AuthType.NONE.value == "none"
    assert AuthType.BASIC.value == "basic"
    assert AuthType.DIGEST.value == "digest"


def test_endpoint_type_enum_values():
    assert EndpointType.GENERIC.value == "generic"
    assert EndpointType.MARKLOGIC.value == "marklogic"
    assert EndpointType.BLAZEGRAPH.value == "blazegraph"
    assert EndpointType.STARDOG.value == "stardog"
    assert EndpointType.FUSEKI.value == "fuseki"
    assert EndpointType.VIRTUOSO.value == "virtuoso"
    assert EndpointType.GRAPHDB.value == "graphdb"


def test_endpoint_profile_creates_with_endpoint_type():
    profile = EndpointProfile(
        url="http://ml.example.com:8050/v1/graphs/sparql",
        endpoint_type=EndpointType.MARKLOGIC,
    )
    assert profile.endpoint_type == EndpointType.MARKLOGIC


def test_endpoint_profile_defaults_to_generic_endpoint_type():
    profile = EndpointProfile(url="https://example.com/sparql")
    assert profile.endpoint_type == EndpointType.GENERIC


def test_endpoint_profile_creates_with_server_specific_params():
    # MarkLogic with database
    ml_profile = EndpointProfile(
        url="http://ml.example.com/sparql",
        endpoint_type=EndpointType.MARKLOGIC,
        database="MarketData",
    )
    assert ml_profile.database == "MarketData"

    # Blazegraph with namespace
    bg_profile = EndpointProfile(
        url="http://blazegraph.example.com/sparql",
        endpoint_type=EndpointType.BLAZEGRAPH,
        namespace="genomics",
    )
    assert bg_profile.namespace == "genomics"

    # Stardog with reasoning
    sd_profile = EndpointProfile(
        url="http://stardog.example.com/query",
        endpoint_type=EndpointType.STARDOG,
        reasoning=True,
    )
    assert sd_profile.reasoning is True

    # GraphDB with repository
    gdb_profile = EndpointProfile(
        url="http://graphdb.example.com/sparql",
        endpoint_type=EndpointType.GRAPHDB,
        repository="corporate-kg",
    )
    assert gdb_profile.repository == "corporate-kg"


# --- AppConfig Tests ---


def test_app_config_creates_with_defaults():
    config = AppConfig()
    assert config.default_endpoint == "wikidata"
    assert config.default_timeout == 30.0
    assert config.default_format == "json"
    assert "wikidata" in config.endpoints


def test_app_config_default_wikidata_endpoint_exists():
    config = AppConfig()
    wikidata = config.endpoints["wikidata"]
    assert wikidata.url == "https://query.wikidata.org/sparql"
    assert wikidata.timeout == 60.0


def test_app_config_creates_with_custom_values():
    config = AppConfig(
        default_endpoint="custom",
        default_timeout=60.0,
        default_format="table",
        endpoints={
            "custom": EndpointProfile(url="https://custom.example.com/sparql"),
        },
    )
    assert config.default_endpoint == "custom"
    assert config.default_timeout == 60.0
    assert config.default_format == "table"


def test_app_config_creates_with_multiple_profiles():
    config = AppConfig(
        endpoints={
            "wikidata": EndpointProfile(
                url="https://query.wikidata.org/sparql",
                timeout=60.0,
            ),
            "dbpedia": EndpointProfile(
                url="https://dbpedia.org/sparql",
            ),
            "private": EndpointProfile(
                url="https://private.example.com/sparql",
                username="admin",
                password="secret",
                auth_type=AuthType.BASIC,
            ),
        }
    )
    assert "wikidata" in config.endpoints
    assert "dbpedia" in config.endpoints
    assert "private" in config.endpoints
    assert config.endpoints["private"].auth_type == AuthType.BASIC


# --- Config Loading Tests ---


def test_config_loading_loads_from_xdg_path(temp_dir, monkeypatch):
    config_dir = temp_dir / ".config" / "sparql"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "config.toml"
    config_file.write_text(
        """
default_endpoint = "test"
default_timeout = 45.0

[endpoints.test]
url = "https://test.example.com/sparql"
timeout = 90.0
"""
    )

    monkeypatch.setenv("HOME", str(temp_dir))

    config = load_config()
    assert config.default_endpoint == "test"
    assert config.default_timeout == 45.0
    assert "test" in config.endpoints
    assert config.endpoints["test"].timeout == 90.0


def test_config_loading_falls_back_to_sparqlrc(temp_dir, monkeypatch):
    sparqlrc = temp_dir / ".sparqlrc"
    sparqlrc.write_text(
        """
default_endpoint = "legacy"

[endpoints.legacy]
url = "https://legacy.example.com/sparql"
"""
    )

    monkeypatch.setenv("HOME", str(temp_dir))

    config = load_config()
    assert config.default_endpoint == "legacy"


def test_config_loading_returns_default_config_when_no_file(temp_dir, monkeypatch):
    monkeypatch.setenv("HOME", str(temp_dir))

    config = load_config()
    assert config.default_endpoint == "wikidata"
    assert "wikidata" in config.endpoints


def test_config_loading_raises_config_error_on_malformed_toml(temp_dir, monkeypatch):
    config_dir = temp_dir / ".config" / "sparql"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "config.toml"
    config_file.write_text("invalid [ toml { content")

    monkeypatch.setenv("HOME", str(temp_dir))

    with pytest.raises(ConfigError, match="Invalid TOML"):
        load_config()


def test_config_loading_loads_endpoint_with_auth(temp_dir, monkeypatch):
    config_dir = temp_dir / ".config" / "sparql"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "config.toml"
    config_file.write_text(
        """
default_endpoint = "private"

[endpoints.private]
url = "https://private.example.com/sparql"
username = "admin"
password = "secret123"  # pragma: allowlist secret
auth_type = "basic"
"""
    )

    monkeypatch.setenv("HOME", str(temp_dir))

    config = load_config()
    profile = config.endpoints["private"]
    assert profile.username == "admin"
    assert profile.password == "secret123"
    assert profile.auth_type == AuthType.BASIC


def test_config_loading_loads_endpoint_with_type_and_params(temp_dir, monkeypatch):
    config_dir = temp_dir / ".config" / "sparql"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "config.toml"
    config_file.write_text(
        """
default_endpoint = "market"

[endpoints.market]
url = "http://ml.example.com/v1/graphs/sparql"
endpoint_type = "marklogic"
database = "MarketData"
timeout = 60.0
auth_type = "digest"
username = "market-reader"
password = "secret"

[endpoints.genes]
url = "http://blazegraph.example.com/sparql"
endpoint_type = "blazegraph"
namespace = "genomics"

[endpoints.products]
url = "http://stardog.example.com/query"
endpoint_type = "stardog"
reasoning = true
"""
    )

    monkeypatch.setenv("HOME", str(temp_dir))

    config = load_config()

    # MarkLogic endpoint
    market = config.endpoints["market"]
    assert market.endpoint_type == EndpointType.MARKLOGIC
    assert market.database == "MarketData"

    # Blazegraph endpoint
    genes = config.endpoints["genes"]
    assert genes.endpoint_type == EndpointType.BLAZEGRAPH
    assert genes.namespace == "genomics"

    # Stardog endpoint
    products = config.endpoints["products"]
    assert products.endpoint_type == EndpointType.STARDOG
    assert products.reasoning is True


# --- Resolve Config Tests ---


def test_resolve_config_uses_default_profile(temp_dir, monkeypatch):
    monkeypatch.setenv("HOME", str(temp_dir))

    config = AppConfig()
    resolved = resolve_config(config)

    assert resolved.endpoint == "https://query.wikidata.org/sparql"
    assert resolved.timeout == 60.0


def test_resolve_config_profile_parameter_overrides_default(temp_dir, monkeypatch):
    monkeypatch.setenv("HOME", str(temp_dir))

    config = AppConfig(
        default_endpoint="wikidata",
        endpoints={
            "wikidata": EndpointProfile(url="https://query.wikidata.org/sparql"),
            "dbpedia": EndpointProfile(
                url="https://dbpedia.org/sparql",
                timeout=45.0,
            ),
        },
    )
    resolved = resolve_config(config, profile="dbpedia")

    assert resolved.endpoint == "https://dbpedia.org/sparql"
    assert resolved.timeout == 45.0


def test_resolve_config_unknown_profile_raises_error(temp_dir, monkeypatch):
    monkeypatch.setenv("HOME", str(temp_dir))

    config = AppConfig()
    with pytest.raises(ConfigError, match="Unknown endpoint"):
        resolve_config(config, profile="nonexistent")


def test_resolve_config_cli_endpoint_overrides_profile(temp_dir, monkeypatch):
    monkeypatch.setenv("HOME", str(temp_dir))

    config = AppConfig()
    resolved = resolve_config(
        config,
        cli_endpoint="https://cli.example.com/sparql",
    )

    assert resolved.endpoint == "https://cli.example.com/sparql"


def test_resolve_config_cli_timeout_overrides_profile(temp_dir, monkeypatch):
    monkeypatch.setenv("HOME", str(temp_dir))

    config = AppConfig()
    resolved = resolve_config(config, cli_timeout=120.0)

    assert resolved.timeout == 120.0


def test_resolve_config_profile_auth_is_resolved(temp_dir, monkeypatch):
    monkeypatch.setenv("HOME", str(temp_dir))

    config = AppConfig(
        default_endpoint="private",
        endpoints={
            "private": EndpointProfile(
                url="https://private.example.com/sparql",
                username="admin",
                password="secret",
                auth_type=AuthType.DIGEST,
            ),
        },
    )
    resolved = resolve_config(config)

    assert resolved.username == "admin"
    assert resolved.password == "secret"
    assert resolved.auth_type == AuthType.DIGEST


def test_resolve_config_cli_auth_overrides_profile(temp_dir, monkeypatch):
    monkeypatch.setenv("HOME", str(temp_dir))

    config = AppConfig(
        default_endpoint="private",
        endpoints={
            "private": EndpointProfile(
                url="https://private.example.com/sparql",
                username="config_user",
                password="config_pass",  # pragma: allowlist secret
                auth_type=AuthType.BASIC,
            ),
        },
    )
    resolved = resolve_config(
        config,
        cli_username="cli_user",
        cli_password="cli_pass",  # pragma: allowlist secret
        cli_auth_type=AuthType.DIGEST,
    )

    assert resolved.username == "cli_user"
    assert resolved.password == "cli_pass"
    assert resolved.auth_type == AuthType.DIGEST


def test_resolve_config_resolves_endpoint_type(temp_dir, monkeypatch):
    monkeypatch.setenv("HOME", str(temp_dir))

    config = AppConfig(
        default_endpoint="market",
        endpoints={
            "market": EndpointProfile(
                url="http://marklogic.example.com/sparql",
                endpoint_type=EndpointType.MARKLOGIC,
            ),
        },
    )
    resolved = resolve_config(config)

    assert resolved.endpoint_type == EndpointType.MARKLOGIC


def test_resolve_config_resolves_server_specific_params(temp_dir, monkeypatch):
    monkeypatch.setenv("HOME", str(temp_dir))

    config = AppConfig(
        default_endpoint="market",
        endpoints={
            "market": EndpointProfile(
                url="http://marklogic.example.com/sparql",
                endpoint_type=EndpointType.MARKLOGIC,
                database="MarketData",
                auth_type=AuthType.DIGEST,
                username="admin",
                password="secret",
            ),
        },
    )
    resolved = resolve_config(config)

    assert resolved.endpoint_type == EndpointType.MARKLOGIC
    assert resolved.database == "MarketData"
    assert resolved.auth_type == AuthType.DIGEST


def test_resolve_config_resolves_blazegraph_namespace(temp_dir, monkeypatch):
    monkeypatch.setenv("HOME", str(temp_dir))

    config = AppConfig(
        default_endpoint="genes",
        endpoints={
            "genes": EndpointProfile(
                url="http://blazegraph.example.com/sparql",
                endpoint_type=EndpointType.BLAZEGRAPH,
                namespace="genomics",
            ),
        },
    )
    resolved = resolve_config(config)

    assert resolved.endpoint_type == EndpointType.BLAZEGRAPH
    assert resolved.namespace == "genomics"


def test_resolve_config_resolves_stardog_reasoning(temp_dir, monkeypatch):
    monkeypatch.setenv("HOME", str(temp_dir))

    config = AppConfig(
        default_endpoint="products",
        endpoints={
            "products": EndpointProfile(
                url="http://stardog.example.com/query",
                endpoint_type=EndpointType.STARDOG,
                reasoning=True,
            ),
        },
    )
    resolved = resolve_config(config)

    assert resolved.endpoint_type == EndpointType.STARDOG
    assert resolved.reasoning is True


# --- Environment Variables Tests ---


def test_env_sparql_profile_env_overrides_default(temp_dir, monkeypatch):
    config_dir = temp_dir / ".config" / "sparql"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "config.toml"
    config_file.write_text(
        """
default_endpoint = "wikidata"

[endpoints.wikidata]
url = "https://query.wikidata.org/sparql"

[endpoints.dbpedia]
url = "https://dbpedia.org/sparql"
"""
    )

    monkeypatch.setenv("HOME", str(temp_dir))
    monkeypatch.setenv("SPARQL_PROFILE", "dbpedia")

    config = load_config()
    resolved = resolve_config(config)

    assert resolved.endpoint == "https://dbpedia.org/sparql"


def test_env_sparql_endpoint_env_overrides_profile(temp_dir, monkeypatch):
    monkeypatch.setenv("HOME", str(temp_dir))
    monkeypatch.setenv("SPARQL_ENDPOINT", "https://env.example.com/sparql")

    config = AppConfig()
    resolved = resolve_config(config)

    assert resolved.endpoint == "https://env.example.com/sparql"


def test_env_sparql_timeout_env_overrides_profile(temp_dir, monkeypatch):
    monkeypatch.setenv("HOME", str(temp_dir))
    monkeypatch.setenv("SPARQL_TIMEOUT", "120")

    config = AppConfig()
    resolved = resolve_config(config)

    assert resolved.timeout == 120.0


def test_env_sparql_user_and_password_env(temp_dir, monkeypatch):
    monkeypatch.setenv("HOME", str(temp_dir))
    monkeypatch.setenv("SPARQL_USER", "env_user")
    monkeypatch.setenv("SPARQL_PASSWORD", "env_pass")

    config = AppConfig()
    resolved = resolve_config(config)

    assert resolved.username == "env_user"
    assert resolved.password == "env_pass"  # pragma: allowlist secret


def test_env_cli_overrides_env_vars(temp_dir, monkeypatch):
    monkeypatch.setenv("HOME", str(temp_dir))
    monkeypatch.setenv("SPARQL_ENDPOINT", "https://env.example.com/sparql")
    monkeypatch.setenv("SPARQL_TIMEOUT", "120")
    monkeypatch.setenv("SPARQL_USER", "env_user")

    config = AppConfig()
    resolved = resolve_config(
        config,
        cli_endpoint="https://cli.example.com/sparql",
        cli_timeout=30.0,
        cli_username="cli_user",
    )

    assert resolved.endpoint == "https://cli.example.com/sparql"
    assert resolved.timeout == 30.0
    assert resolved.username == "cli_user"


# --- Config Precedence Tests ---


def test_precedence_full_precedence_chain(temp_dir, monkeypatch):
    """Test full precedence chain: CLI > Env > Profile > Default."""
    config_dir = temp_dir / ".config" / "sparql"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "config.toml"
    config_file.write_text(
        """
default_endpoint = "configured"
default_timeout = 10.0

[endpoints.configured]
url = "https://config.example.com/sparql"
timeout = 20.0
username = "config_user"
"""
    )

    monkeypatch.setenv("HOME", str(temp_dir))
    monkeypatch.setenv("SPARQL_TIMEOUT", "30")
    monkeypatch.setenv("SPARQL_USER", "env_user")

    config = load_config()
    resolved = resolve_config(
        config,
        cli_timeout=40.0,
    )

    # CLI timeout wins
    assert resolved.timeout == 40.0
    # Env user wins over config
    assert resolved.username == "env_user"
    # Profile URL (no override)
    assert resolved.endpoint == "https://config.example.com/sparql"
