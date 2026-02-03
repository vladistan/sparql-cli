"""CSV and TSV formatters with optional header row."""

from __future__ import annotations

import csv
import io
from collections.abc import Iterator
from typing import TYPE_CHECKING

from sparql.core.models import QueryResult
from sparql.formatters.base import FormatterBase

if TYPE_CHECKING:
    from sparql.core.prefixes import PrefixResolver


class CSVFormatter(FormatterBase):
    """Formats results as CSV with proper escaping per RFC 4180."""

    def __init__(
        self,
        skip_header: bool = False,
        prefix_resolver: PrefixResolver | None = None,
    ) -> None:
        self.skip_header = skip_header
        self._prefix_resolver = prefix_resolver

    def format(self, results: Iterator[QueryResult]) -> Iterator[str]:
        """Format query results as RFC 4180 CSV with optional header row."""
        results_list = list(results)

        if not results_list:
            return

        variables = self._collect_variables(results_list)

        output = io.StringIO()
        writer = csv.writer(output)

        if not self.skip_header:
            writer.writerow(variables)
            yield output.getvalue().rstrip()
            output.truncate(0)
            output.seek(0)

        for result in results_list:
            row = [
                self._abbreviate(result.bindings[var].value)
                if var in result.bindings
                else ""
                for var in variables
            ]
            writer.writerow(row)
            yield output.getvalue().rstrip()
            output.truncate(0)
            output.seek(0)


class TSVFormatter(FormatterBase):
    """Formats results as TSV (tab-separated values)."""

    def __init__(
        self,
        skip_header: bool = False,
        prefix_resolver: PrefixResolver | None = None,
    ) -> None:
        self.skip_header = skip_header
        self._prefix_resolver = prefix_resolver

    def format(self, results: Iterator[QueryResult]) -> Iterator[str]:
        """Format query results as tab-separated values with optional header."""
        results_list = list(results)

        if not results_list:
            return

        variables = self._collect_variables(results_list)

        if not self.skip_header:
            yield "\t".join(variables)

        for result in results_list:
            row = [
                self._abbreviate(result.bindings[var].value)
                if var in result.bindings
                else ""
                for var in variables
            ]
            yield "\t".join(row)
