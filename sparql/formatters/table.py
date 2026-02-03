"""Table formatter using Rich for terminal output."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from rich.console import Console
from rich.table import Table

from sparql.core.models import QueryResult
from sparql.formatters.base import FormatterBase

if TYPE_CHECKING:
    from sparql.core.prefixes import PrefixResolver

# Default maximum column width for truncation
DEFAULT_MAX_WIDTH = 40


class TableFormatter(FormatterBase):
    """Formats results as a Rich table with truncated columns."""

    def __init__(
        self,
        max_width: int = DEFAULT_MAX_WIDTH,
        prefix_resolver: PrefixResolver | None = None,
    ) -> None:
        self.max_width = max_width
        self._prefix_resolver = prefix_resolver

    def format(self, results: Iterator[QueryResult]) -> Iterator[str]:
        """Format results as Rich table with truncated columns.

        Table headers come from variable names. Values truncated at max_width.
        URIs are abbreviated using prefixes before truncation.
        Empty results yield "No results" message.
        """
        results_list = list(results)

        if not results_list:
            yield "No results"
            return

        variables = self._collect_variables(results_list)

        # Build Rich table
        table = Table(show_header=True, header_style="bold")

        for var in variables:
            table.add_column(var)

        for result in results_list:
            row = []
            for var in variables:
                if var in result.bindings:
                    # Abbreviate URIs before truncation
                    value = self._abbreviate(result.bindings[var].value)
                    # Truncate wide values with ellipsis
                    if len(value) > self.max_width:
                        value = value[: self.max_width - 3] + "..."
                    row.append(value)
                else:
                    row.append("")
            table.add_row(*row)

        # Render table to string
        console = Console()
        with console.capture() as capture:
            console.print(table)

        yield capture.get().rstrip()
