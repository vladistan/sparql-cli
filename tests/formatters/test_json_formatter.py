import json

from sparql.core.models import BindingValue, QueryResult
from sparql.formatters.json import JSONFormatter, Sparql11Formatter

# =============================================================================
# Sparql11Formatter Tests (SPARQL 1.1 JSON Format)
# =============================================================================


def test_sparql11_formatter_empty_results():
    formatter = Sparql11Formatter()
    results = []

    output = list(formatter.format(iter(results)))

    assert len(output) == 1
    data = json.loads(output[0])
    assert data["head"]["vars"] == []
    assert data["results"]["bindings"] == []


def test_sparql11_formatter_single_result():
    formatter = Sparql11Formatter()
    results = [
        QueryResult(
            bindings={
                "s": BindingValue(type="uri", value="http://example.org/subject"),
                "p": BindingValue(type="uri", value="http://example.org/predicate"),
                "o": BindingValue(type="literal", value="object value"),
            }
        )
    ]

    output = list(formatter.format(iter(results)))

    assert len(output) == 1
    data = json.loads(output[0])
    assert set(data["head"]["vars"]) == {"s", "p", "o"}
    assert len(data["results"]["bindings"]) == 1
    assert data["results"]["bindings"][0]["s"]["value"] == "http://example.org/subject"


def test_sparql11_formatter_compact_mode():
    formatter = Sparql11Formatter(compact=True)
    results = [
        QueryResult(bindings={"x": BindingValue(type="literal", value="test")})
    ]

    output = list(formatter.format(iter(results)))

    assert len(output) == 1
    # Compact should have no spaces after separators
    assert ',"results":{' in output[0]


def test_sparql11_formatter_pretty_print_mode():
    formatter = Sparql11Formatter(compact=False)
    results = [
        QueryResult(bindings={"x": BindingValue(type="literal", value="test")})
    ]

    output = list(formatter.format(iter(results)))

    assert len(output) == 1
    # Pretty print should have indentation
    assert "\n" in output[0]
    assert "  " in output[0]


def test_sparql11_formatter_with_datatype():
    formatter = Sparql11Formatter()
    results = [
        QueryResult(
            bindings={
                "value": BindingValue(
                    type="typed-literal",
                    value="42",
                    datatype="http://www.w3.org/2001/XMLSchema#integer",
                )
            }
        )
    ]

    output = list(formatter.format(iter(results)))

    data = json.loads(output[0])
    binding = data["results"]["bindings"][0]["value"]
    assert binding["datatype"] == "http://www.w3.org/2001/XMLSchema#integer"


def test_sparql11_formatter_with_language():
    formatter = Sparql11Formatter()
    results = [
        QueryResult(
            bindings={
                "label": BindingValue(type="literal", value="Hello", xml_lang="en")
            }
        )
    ]

    output = list(formatter.format(iter(results)))

    data = json.loads(output[0])
    binding = data["results"]["bindings"][0]["label"]
    assert binding["xml:lang"] == "en"


# =============================================================================
# JSONFormatter Tests (Simple Object Notation)
# =============================================================================


def test_json_formatter_empty_results():
    formatter = JSONFormatter()
    results = []

    output = list(formatter.format(iter(results)))

    assert len(output) == 1
    data = json.loads(output[0])
    assert data == []


def test_json_formatter_single_result():
    formatter = JSONFormatter()
    results = [
        QueryResult(
            bindings={
                "name": BindingValue(type="literal", value="Alice"),
                "age": BindingValue(type="literal", value="30"),
            }
        )
    ]

    output = list(formatter.format(iter(results)))

    assert len(output) == 1
    data = json.loads(output[0])
    assert len(data) == 1
    assert data[0]["name"] == "Alice"
    assert data[0]["age"] == "30"


def test_json_formatter_multiple_results():
    formatter = JSONFormatter()
    results = [
        QueryResult(
            bindings={
                "name": BindingValue(type="literal", value="Alice"),
                "age": BindingValue(type="literal", value="30"),
            }
        ),
        QueryResult(
            bindings={
                "name": BindingValue(type="literal", value="Bob"),
                "age": BindingValue(type="literal", value="25"),
            }
        ),
    ]

    output = list(formatter.format(iter(results)))

    assert len(output) == 1
    data = json.loads(output[0])
    assert len(data) == 2
    assert data[0]["name"] == "Alice"
    assert data[1]["name"] == "Bob"


def test_json_formatter_jsonl_mode():
    formatter = JSONFormatter(jsonl=True)
    results = [
        QueryResult(
            bindings={
                "name": BindingValue(type="literal", value="Alice"),
                "age": BindingValue(type="literal", value="30"),
            }
        ),
        QueryResult(
            bindings={
                "name": BindingValue(type="literal", value="Bob"),
                "age": BindingValue(type="literal", value="25"),
            }
        ),
    ]

    output = list(formatter.format(iter(results)))

    # JSONL mode yields one line per result
    assert len(output) == 2
    line1 = json.loads(output[0])
    line2 = json.loads(output[1])
    assert line1["name"] == "Alice"
    assert line2["name"] == "Bob"


def test_json_formatter_jsonl_is_compact():
    formatter = JSONFormatter(jsonl=True)
    results = [
        QueryResult(
            bindings={"name": BindingValue(type="literal", value="Alice")}
        )
    ]

    output = list(formatter.format(iter(results)))

    # JSONL should be compact (no spaces)
    assert output[0] == '{"name":"Alice"}'


def test_json_formatter_suitable_for_pandas():
    """Verify JSON output can be loaded directly by pandas."""
    formatter = JSONFormatter()
    results = [
        QueryResult(
            bindings={
                "name": BindingValue(type="literal", value="Alice"),
                "age": BindingValue(type="literal", value="30"),
            }
        ),
        QueryResult(
            bindings={
                "name": BindingValue(type="literal", value="Bob"),
                "age": BindingValue(type="literal", value="25"),
            }
        ),
    ]

    output = list(formatter.format(iter(results)))
    data = json.loads(output[0])

    # This format works with: pd.DataFrame(data)
    assert isinstance(data, list)
    assert all(isinstance(row, dict) for row in data)
    assert all("name" in row and "age" in row for row in data)
