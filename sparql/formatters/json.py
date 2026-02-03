"""JSON formatters for SPARQL query results."""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import TYPE_CHECKING

from sparql.core.models import QueryResult
from sparql.formatters.base import FormatterBase

if TYPE_CHECKING:
    from sparql.core.prefixes import PrefixResolver


class Sparql11Formatter(FormatterBase):
    """Formats results following SPARQL 1.1 Query Results JSON Format specification."""

    def __init__(
        self,
        compact: bool = False,
        prefix_resolver: PrefixResolver | None = None,
    ) -> None:
        self.compact = compact
        self._prefix_resolver = prefix_resolver

    def _binding_to_dict(self, result: QueryResult) -> dict[str, dict[str, str]]:
        """Convert a QueryResult to SPARQL 1.1 JSON binding format."""
        binding_dict: dict[str, dict[str, str]] = {}
        for var, binding in result.bindings.items():
            entry: dict[str, str] = {
                "type": binding.type,
                "value": self._abbreviate(binding.value),
            }
            if binding.datatype:
                entry["datatype"] = binding.datatype
            if binding.xml_lang:
                entry["xml:lang"] = binding.xml_lang
            binding_dict[var] = entry
        return binding_dict

    def format(self, results: Iterator[QueryResult]) -> Iterator[str]:
        """Format results as SPARQL 1.1 Query Results JSON Format."""
        results_list = list(results)

        variables = list(results_list[0].bindings.keys()) if results_list else []

        output = {
            "head": {"vars": variables},
            "results": {
                "bindings": [
                    self._binding_to_dict(result)
                    for result in results_list
                ]
            },
        }

        if self.compact:
            yield json.dumps(output, separators=(",", ":"))
        else:
            yield json.dumps(output, indent=2)


class JSONFormatter(FormatterBase):
    """Formats results as simple objects with variable names as keys.

    Supports two modes:
    - JSON array: [{var: value, ...}, ...] - valid JSON, suitable for pandas
    - JSONL: one object per line for streaming pipelines
    """

    def __init__(
        self,
        jsonl: bool = False,
        prefix_resolver: PrefixResolver | None = None,
    ) -> None:
        self.jsonl = jsonl
        self._prefix_resolver = prefix_resolver

    def format(self, results: Iterator[QueryResult]) -> Iterator[str]:
        """Format results as JSON array or JSONL depending on mode."""
        if self.jsonl:
            # JSONL mode: one compact object per line
            for result in results:
                obj = {
                    var: self._abbreviate(binding.value)
                    for var, binding in result.bindings.items()
                }
                yield json.dumps(obj, separators=(",", ":"))
        else:
            # JSON array mode: collect all and output valid JSON array
            results_list = list(results)
            objects = [
                {
                    var: self._abbreviate(binding.value)
                    for var, binding in result.bindings.items()
                }
                for result in results_list
            ]
            yield json.dumps(objects, indent=2)
