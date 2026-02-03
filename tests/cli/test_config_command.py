import json

from typer.testing import CliRunner

from sparql.cli.main import app

runner = CliRunner()


def test_config_show_shows_default_config_when_no_file(temp_dir, monkeypatch):
    monkeypatch.setenv("HOME", str(temp_dir))

    result = runner.invoke(app, ["config", "show"])

    assert result.exit_code == 0
    assert "wikidata" in result.output.lower()
    assert "https://query.wikidata.org/sparql" in result.output


def test_config_show_shows_config_file_values(temp_dir, monkeypatch):
    config_dir = temp_dir / ".config" / "sparql"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "config.toml"
    config_file.write_text(
        """
default_endpoint = "custom"

[endpoints.custom]
url = "https://custom.example.com/sparql"
timeout = 60.0
"""
    )

    monkeypatch.setenv("HOME", str(temp_dir))

    result = runner.invoke(app, ["config", "show"])

    assert result.exit_code == 0
    assert "custom" in result.output
    assert "https://custom.example.com/sparql" in result.output


def test_config_show_shows_configured_profiles(temp_dir, monkeypatch):
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

    result = runner.invoke(app, ["config", "show"])

    assert result.exit_code == 0
    assert "wikidata" in result.output
    assert "dbpedia" in result.output


def test_config_show_shows_auth_info_for_private_endpoints(temp_dir, monkeypatch):
    config_dir = temp_dir / ".config" / "sparql"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "config.toml"
    config_file.write_text(
        """
default_endpoint = "private"

[endpoints.private]
url = "https://private.example.com/sparql"
username = "admin"
password = "secret"  # pragma: allowlist secret
auth_type = "basic"
"""
    )

    monkeypatch.setenv("HOME", str(temp_dir))

    result = runner.invoke(app, ["config", "show"])

    assert result.exit_code == 0
    assert "basic" in result.output
    assert "admin" in result.output
    # Password should be masked
    assert "secret" not in result.output
    assert "***" in result.output


def test_config_show_json_output_format(temp_dir, monkeypatch):
    config_dir = temp_dir / ".config" / "sparql"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "config.toml"
    config_file.write_text(
        """
default_endpoint = "test"

[endpoints.test]
url = "https://test.example.com/sparql"
"""
    )

    monkeypatch.setenv("HOME", str(temp_dir))

    result = runner.invoke(app, ["config", "show", "--json"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "effective" in data
    assert "profiles" in data
    assert data["default_endpoint"] == "test"
