"""Query source resolution for SPARQL CLI.

Resolves query text from multiple sources with priority:
1. Inline query (-e flag)
2. File path argument (or inline SPARQL if it looks like a query)
3. Standard input
"""

from pathlib import Path
from typing import TextIO

from sparql.core.exceptions import ConfigError


def resolve_query_source(
    inline: str | None,
    file_path: str | Path | None,
    stdin: TextIO | None,
) -> str:
    """Resolve query from inline, file, or stdin with precedence order.

    Raises ConfigError if no query source provided or file not found.
    """
    # Priority 1: Inline query
    if inline is not None:
        query = inline.strip()
        if not query:
            raise ConfigError("Empty query provided. Provide a valid SPARQL query.")
        return query

    # Priority 2: File path (or inline query if it looks like SPARQL)
    if file_path is not None:
        # Convert to string first to check for inline SPARQL
        # (must happen before Path conversion to preserve // in URLs)
        path_str = str(file_path)
        sparql_keywords = ("SELECT", "ASK", "CONSTRUCT", "DESCRIBE", "PREFIX")
        if path_str.upper().startswith(sparql_keywords):
            return path_str.strip()
        # It's a file path
        path = file_path if isinstance(file_path, Path) else Path(file_path)
        if not path.exists():
            raise ConfigError(f"Query file not found: {file_path}")
        query = path.read_text().strip()
        if not query:
            raise ConfigError(f"Query file is empty: {file_path}")
        return query

    # Priority 3: Standard input
    if stdin is not None:
        content = stdin.read()
        query = content.strip() if content else ""
        if query:
            return query

    raise ConfigError("No query provided. Use -e, provide a file, or pipe to stdin.")
