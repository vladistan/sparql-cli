from sparql.core.models import BindingValue, QueryResult
from sparql.formatters.csv import CSVFormatter, TSVFormatter

# =============================================================================
# CSVFormatter Tests
# =============================================================================


def test_csv_formatter_empty_results():
    formatter = CSVFormatter()
    results = []

    output = list(formatter.format(iter(results)))

    assert len(output) == 0


def test_csv_formatter_single_result():
    formatter = CSVFormatter()
    results = [
        QueryResult(
            bindings={
                "name": BindingValue(type="literal", value="Alice"),
                "age": BindingValue(type="literal", value="30"),
            }
        )
    ]

    output = list(formatter.format(iter(results)))

    assert len(output) == 2  # Header + 1 data row
    assert "name" in output[0] and "age" in output[0]
    assert "Alice" in output[1] and "30" in output[1]


def test_csv_formatter_escapes_commas():
    formatter = CSVFormatter()
    results = [
        QueryResult(
            bindings={
                "value": BindingValue(type="literal", value="Hello, World"),
            }
        )
    ]

    output = list(formatter.format(iter(results)))

    # CSV should quote values containing commas
    assert '"Hello, World"' in output[1]


def test_csv_formatter_escapes_quotes():
    formatter = CSVFormatter()
    results = [
        QueryResult(
            bindings={
                "value": BindingValue(type="literal", value='Say "Hello"'),
            }
        )
    ]

    output = list(formatter.format(iter(results)))

    # CSV should escape quotes by doubling them
    assert '""' in output[1]


def test_csv_formatter_multiple_results():
    formatter = CSVFormatter()
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

    assert len(output) == 3  # Header + 2 data rows


def test_csv_formatter_skip_header():
    formatter = CSVFormatter(skip_header=True)
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

    # No header row, just 2 data rows
    assert len(output) == 2
    # First row should be data, not headers
    assert "Alice" in output[0]
    assert "Bob" in output[1]


def test_csv_formatter_missing_binding():
    formatter = CSVFormatter()
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
                # age missing
            }
        ),
    ]

    output = list(formatter.format(iter(results)))

    # Should handle missing values gracefully
    assert len(output) == 3
    # Second row should have empty value for age
    assert "Bob" in output[2]


# =============================================================================
# TSVFormatter Tests
# =============================================================================


def test_tsv_formatter_empty_results():
    formatter = TSVFormatter()
    results = []

    output = list(formatter.format(iter(results)))

    assert len(output) == 0


def test_tsv_formatter_single_result():
    formatter = TSVFormatter()
    results = [
        QueryResult(
            bindings={
                "name": BindingValue(type="literal", value="Alice"),
                "age": BindingValue(type="literal", value="30"),
            }
        )
    ]

    output = list(formatter.format(iter(results)))

    assert len(output) == 2  # Header + 1 data row
    assert "\t" in output[0]
    assert "\t" in output[1]
    assert "Alice" in output[1] and "30" in output[1]


def test_tsv_formatter_multiple_results():
    formatter = TSVFormatter()
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

    assert len(output) == 3  # Header + 2 data rows


def test_tsv_formatter_skip_header():
    formatter = TSVFormatter(skip_header=True)
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

    # No header row, just 2 data rows
    assert len(output) == 2
    # First row should be data, not headers
    assert "Alice" in output[0]
    assert "Bob" in output[1]
