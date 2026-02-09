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


def test_binding_value_coerces_float_to_string():
    """Float values from xsd:double datatypes should be coerced to strings.

    Some SPARQL endpoints return numeric values as Python floats in JSON
    responses (e.g., DBpedia with xsd:double literals like wavelength).
    """
    from sparql.core.models import BindingValue

    data = {
        "type": "typed-literal",
        "value": 4.95e-07,  # Float, not string
        "datatype": "http://www.w3.org/2001/XMLSchema#double",
    }
    result = BindingValue(**data)

    assert result.type == "typed-literal"
    assert result.value == "4.95e-07"
    assert result.datatype == "http://www.w3.org/2001/XMLSchema#double"


def test_binding_value_coerces_int_to_string():
    """Integer values should be coerced to strings."""
    from sparql.core.models import BindingValue

    data = {
        "type": "typed-literal",
        "value": 42,  # Int, not string
        "datatype": "http://www.w3.org/2001/XMLSchema#integer",
    }
    result = BindingValue(**data)

    assert result.type == "typed-literal"
    assert result.value == "42"


def test_binding_value_preserves_string_value():
    """String values should pass through unchanged."""
    from sparql.core.models import BindingValue

    data = {
        "type": "typed-literal",
        "value": "42",
        "datatype": "http://www.w3.org/2001/XMLSchema#integer",
    }
    result = BindingValue(**data)

    assert result.value == "42"


def test_update_result_holds_success_status():
    """Test UpdateResult model stores success status."""
    from sparql.core.models import UpdateResult

    result = UpdateResult(success=True, status_code=200, message="Update successful")

    assert result.success is True
    assert result.status_code == 200
    assert result.message == "Update successful"


def test_update_result_holds_failure_status():
    """Test UpdateResult model stores failure status."""
    from sparql.core.models import UpdateResult

    result = UpdateResult(
        success=False, status_code=400, message="Bad Request: Invalid syntax"
    )

    assert result.success is False
    assert result.status_code == 400
    assert result.message == "Bad Request: Invalid syntax"


def test_update_result_requires_all_fields():
    """Test UpdateResult model requires all fields."""
    from sparql.core.models import UpdateResult

    with pytest.raises(ValidationError):
        UpdateResult(success=True, status_code=200)  # Missing message
