import pytest

from sparql.formatters import get_formatter, list_formatters


def test_list_formatters_returns_all():
    formatters = list_formatters()

    assert "json" in formatters
    assert "jsonl" in formatters
    assert "sparql11" in formatters
    assert "table" in formatters
    assert "csv" in formatters
    assert "tsv" in formatters


def test_get_formatter_json():
    formatter_class = get_formatter("json")

    assert formatter_class.__name__ == "JSONFormatter"


def test_get_formatter_jsonl():
    formatter_class = get_formatter("jsonl")

    # JSONL uses same class as JSON, just with different default
    assert formatter_class.__name__ == "JSONFormatter"


def test_get_formatter_sparql11():
    formatter_class = get_formatter("sparql11")

    assert formatter_class.__name__ == "Sparql11Formatter"


def test_get_formatter_table():
    formatter_class = get_formatter("table")

    assert formatter_class.__name__ == "TableFormatter"


def test_get_formatter_csv():
    formatter_class = get_formatter("csv")

    assert formatter_class.__name__ == "CSVFormatter"


def test_get_formatter_tsv():
    formatter_class = get_formatter("tsv")

    assert formatter_class.__name__ == "TSVFormatter"


def test_get_formatter_unknown_raises():
    with pytest.raises(KeyError):
        get_formatter("unknown")
