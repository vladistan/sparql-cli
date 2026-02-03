"""Shared output format definitions for CLI commands."""

from enum import Enum


class OutputFormat(str, Enum):
    json = "json"
    jsonl = "jsonl"
    sparql11 = "sparql11"
    table = "table"
    csv = "csv"
    tsv = "tsv"
