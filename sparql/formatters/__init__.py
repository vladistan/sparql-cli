"""Output formatters for SPARQL query results.

Formatters convert QueryResult streams to various text formats.
All formatters are registered in the formatter registry for lookup by name.
"""

from sparql.formatters.base import (
    Formatter,
    FormatterBase,
    get_formatter,
    list_formatters,
    register_formatter,
)
from sparql.formatters.csv import CSVFormatter, TSVFormatter
from sparql.formatters.json import JSONFormatter, Sparql11Formatter
from sparql.formatters.table import TableFormatter

# Register all formatters
register_formatter("json", JSONFormatter)
register_formatter("jsonl", JSONFormatter)  # Same class, different default
register_formatter("sparql11", Sparql11Formatter)
register_formatter("table", TableFormatter)
register_formatter("csv", CSVFormatter)
register_formatter("tsv", TSVFormatter)

__all__ = [
    "Formatter",
    "FormatterBase",
    "JSONFormatter",
    "Sparql11Formatter",
    "TableFormatter",
    "CSVFormatter",
    "TSVFormatter",
    "get_formatter",
    "list_formatters",
    "register_formatter",
]
