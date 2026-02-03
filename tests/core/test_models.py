"""Tests for SPARQL CLI Pydantic models (Step 2.1)."""

import pytest
from pydantic import ValidationError


def test_binding_value_parses_uri_type():
    from sparql.core.models import BindingValue

    data = {"type": "uri", "value": "http://example.org/resource"}
    result = BindingValue(**data)

    assert result.type == "uri"
    assert result.value == "http://example.org/resource"
    assert result.datatype is None
    assert result.xml_lang is None


def test_binding_value_parses_literal_with_datatype():
    from sparql.core.models import BindingValue

    data = {
        "type": "typed-literal",
        "value": "42",
        "datatype": "http://www.w3.org/2001/XMLSchema#integer",
    }
    result = BindingValue(**data)

    assert result.type == "typed-literal"
    assert result.value == "42"
    assert result.datatype == "http://www.w3.org/2001/XMLSchema#integer"


def test_binding_value_parses_literal_with_lang():
    from sparql.core.models import BindingValue

    data = {"type": "literal", "value": "Hello", "xml:lang": "en"}
    result = BindingValue(**data)

    assert result.type == "literal"
    assert result.value == "Hello"
    assert result.xml_lang == "en"


def test_binding_value_parses_bnode():
    from sparql.core.models import BindingValue

    data = {"type": "bnode", "value": "b0"}
    result = BindingValue(**data)

    assert result.type == "bnode"
    assert result.value == "b0"


def test_binding_value_rejects_invalid_type():
    from sparql.core.models import BindingValue

    data = {"type": "invalid", "value": "test"}

    with pytest.raises(ValidationError):
        BindingValue(**data)


def test_query_result_holds_bindings():
    from sparql.core.models import BindingValue, QueryResult

    binding = BindingValue(type="uri", value="http://example.org")
    result = QueryResult(bindings={"s": binding})

    assert "s" in result.bindings
    assert result.bindings["s"].value == "http://example.org"


def test_query_result_accepts_empty_bindings():
    from sparql.core.models import QueryResult

    result = QueryResult(bindings={})

    assert result.bindings == {}


def test_endpoint_config_validates_url_format():
    from sparql.core.models import EndpointConfig

    config = EndpointConfig(url="https://query.wikidata.org/sparql")

    assert str(config.url) == "https://query.wikidata.org/sparql"


def test_endpoint_config_rejects_invalid_url():
    from sparql.core.models import EndpointConfig

    with pytest.raises(ValidationError):
        EndpointConfig(url="not-a-url")


def test_endpoint_config_has_defaults():
    from sparql.core.models import EndpointConfig

    config = EndpointConfig(url="https://example.org/sparql")

    assert config.timeout == 30.0
    assert config.user_agent == "sparql-cli/1.0"


def test_endpoint_config_accepts_custom_timeout():
    from sparql.core.models import EndpointConfig

    config = EndpointConfig(url="https://example.org/sparql", timeout=60.0)

    assert config.timeout == 60.0


def test_endpoint_config_rejects_negative_timeout():
    from sparql.core.models import EndpointConfig

    with pytest.raises(ValidationError):
        EndpointConfig(url="https://example.org/sparql", timeout=-1.0)
