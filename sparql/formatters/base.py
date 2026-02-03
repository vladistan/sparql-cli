"""Formatter protocol, base class, and registry for SPARQL query results."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Protocol

from sparql.core.models import QueryResult

if TYPE_CHECKING:
    from sparql.core.prefixes import PrefixResolver


class Formatter(Protocol):
    """Protocol for output formatters that convert QueryResult streams to text.

    Formatters accept an iterator of query results and yield formatted output lines.
    Implementation is pluggable via the formatter registry.
    """

    def format(self, results: Iterator[QueryResult]) -> Iterator[str]:
        ...


class FormatterBase:
    """Base class providing shared functionality for formatters.

    Subclasses should set _prefix_resolver in __init__ to enable URI abbreviation.
    """

    _prefix_resolver: PrefixResolver | None = None

    def _abbreviate(self, value: str) -> str:
        """Abbreviate URI using configured prefix resolver if available."""
        if self._prefix_resolver:
            return self._prefix_resolver.abbreviate(value)
        return value

    def _collect_variables(
        self, results_list: list[QueryResult]
    ) -> list[str]:
        """Collect variable names preserving SELECT order when available.

        Uses head.vars from first result if present, otherwise collects
        all variables across results to handle OPTIONAL bindings.
        """
        if not results_list:
            return []

        if results_list[0].variables:
            return results_list[0].variables

        # Fallback: collect ALL variables across all results (for OPTIONAL)
        all_vars: set[str] = set()
        for result in results_list:
            all_vars.update(result.bindings.keys())
        variables = list(results_list[0].bindings.keys())
        for var in all_vars:
            if var not in variables:
                variables.append(var)
        return variables


_FORMATTERS: dict[str, type[Formatter]] = {}


def register_formatter(name: str, formatter_class: type[Formatter]) -> None:
    _FORMATTERS[name] = formatter_class


def get_formatter(name: str) -> type[Formatter]:
    return _FORMATTERS[name]


def list_formatters() -> list[str]:
    return list(_FORMATTERS.keys())
