"""Query source resolution for SPARQL CLI.

Resolves query text from multiple sources with priority:
1. Inline query (-e flag)
2. File path argument (or inline SPARQL if it looks like a query)
3. Standard input
"""

from pathlib import Path
from typing import TextIO

from sparql.core.exceptions import ConfigError

_QUERY_KEYWORDS = ("SELECT", "ASK", "CONSTRUCT", "DESCRIBE", "PREFIX")
_UPDATE_KEYWORDS = (
    "INSERT", "DELETE", "LOAD", "CLEAR", "DROP", "CREATE", "COPY", "MOVE", "ADD",
)
_ALL_SPARQL_KEYWORDS = _QUERY_KEYWORDS + _UPDATE_KEYWORDS


def is_update_query(query: str) -> bool:
    """Check whether a SPARQL string is an UPDATE operation.

    Handles PREFIX declarations before the actual UPDATE keyword.
    """
    import re

    # Strip PREFIX declarations (single or multi-line)
    text = re.sub(
        r"(?i)\bPREFIX\s+\S+\s+<[^>]*>\s*", "", query.strip()
    ).strip().upper()
    return text.startswith(_UPDATE_KEYWORDS)


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
        if path_str.upper().startswith(_ALL_SPARQL_KEYWORDS):
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
