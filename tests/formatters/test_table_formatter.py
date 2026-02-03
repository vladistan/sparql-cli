from sparql.core.models import BindingValue, QueryResult
from sparql.formatters.table import TableFormatter


def test_table_formatter_empty_results():
    formatter = TableFormatter()
    results = []

    output = list(formatter.format(iter(results)))

    assert len(output) == 1
    assert output[0] == "No results"


def test_table_formatter_single_result():
    formatter = TableFormatter()
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
    table = output[0]
    assert "name" in table
    assert "age" in table
    assert "Alice" in table
    assert "30" in table


def test_table_formatter_multiple_results():
    formatter = TableFormatter()
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
    table = output[0]
    assert "Alice" in table
    assert "Bob" in table


def test_table_formatter_truncates_wide_values():
    formatter = TableFormatter(max_width=10)
    long_value = "x" * 50
    results = [
        QueryResult(
            bindings={
                "data": BindingValue(type="literal", value=long_value),
            }
        )
    ]

    output = list(formatter.format(iter(results)))

    table = output[0]
    # Should be truncated with ellipsis
    assert "..." in table
    # Full value should not appear
    assert long_value not in table


def test_table_formatter_missing_binding():
    formatter = TableFormatter()
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
                # age missing for Bob
            }
        ),
    ]

    output = list(formatter.format(iter(results)))

    # Should not crash, table should render with empty cell
    assert len(output) == 1
    table = output[0]
    assert "Alice" in table
    assert "Bob" in table
