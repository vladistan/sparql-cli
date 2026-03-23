"""Tests for query source resolution."""

import pytest


def test_resolve_query_from_inline():
    from sparql.core.query_source import resolve_query_source

    result = resolve_query_source(
        inline="SELECT * WHERE { ?s ?p ?o }",
        file_path=None,
        stdin=None,
    )

    assert result == "SELECT * WHERE { ?s ?p ?o }"


def test_resolve_query_from_file(temp_query_file):
    from sparql.core.query_source import resolve_query_source

    result = resolve_query_source(
        inline=None,
        file_path=temp_query_file,
        stdin=None,
    )

    assert "SELECT" in result
    assert "LIMIT 10" in result


def test_resolve_query_from_stdin():
    from io import StringIO

    from sparql.core.query_source import resolve_query_source

    stdin = StringIO("SELECT * WHERE { ?s ?p ?o } LIMIT 5")

    result = resolve_query_source(
        inline=None,
        file_path=None,
        stdin=stdin,
    )

    assert result == "SELECT * WHERE { ?s ?p ?o } LIMIT 5"


def test_resolve_query_inline_takes_precedence(temp_query_file):
    from io import StringIO

    from sparql.core.query_source import resolve_query_source

    stdin = StringIO("FROM STDIN")

    result = resolve_query_source(
        inline="INLINE QUERY",
        file_path=temp_query_file,
        stdin=stdin,
    )

    # Inline should take precedence
    assert result == "INLINE QUERY"


def test_resolve_query_file_takes_precedence_over_stdin(temp_query_file):
    from io import StringIO

    from sparql.core.query_source import resolve_query_source

    stdin = StringIO("FROM STDIN")

    result = resolve_query_source(
        inline=None,
        file_path=temp_query_file,
        stdin=stdin,
    )

    # File should take precedence over stdin
    assert "SELECT" in result
    assert "LIMIT 10" in result


def test_resolve_query_raises_for_nonexistent_file(temp_dir):
    from sparql.core.exceptions import ConfigError
    from sparql.core.query_source import resolve_query_source

    nonexistent = temp_dir / "does_not_exist.rq"

    with pytest.raises(ConfigError) as exc_info:
        resolve_query_source(
            inline=None,
            file_path=nonexistent,
            stdin=None,
        )

    assert "not found" in str(exc_info.value).lower()


def test_resolve_query_raises_when_no_source():
    from sparql.core.exceptions import ConfigError
    from sparql.core.query_source import resolve_query_source

    with pytest.raises(ConfigError) as exc_info:
        resolve_query_source(
            inline=None,
            file_path=None,
            stdin=None,
        )

    assert "no query" in str(exc_info.value).lower()


def test_resolve_query_strips_whitespace():
    from sparql.core.query_source import resolve_query_source

    result = resolve_query_source(
        inline="  SELECT * WHERE { ?s ?p ?o }  \n",
        file_path=None,
        stdin=None,
    )

    assert result == "SELECT * WHERE { ?s ?p ?o }"


# --- UPDATE keyword detection ---


@pytest.mark.parametrize(
    "keyword",
    ["INSERT", "DELETE", "LOAD", "CLEAR", "DROP", "CREATE", "COPY", "MOVE", "ADD"],
)
def test_resolve_query_detects_update_keyword_as_inline(keyword):
    """UPDATE keywords in file_path position should be treated as inline SPARQL."""
    from sparql.core.query_source import resolve_query_source

    query = f"{keyword} DATA {{ <http://ex.org/s> <http://ex.org/p> 'val' }}"
    result = resolve_query_source(inline=None, file_path=query, stdin=None)

    assert result == query


def test_resolve_query_detects_lowercase_update_keyword():
    from sparql.core.query_source import resolve_query_source

    query = "insert data { <http://ex.org/s> <http://ex.org/p> 'val' }"
    result = resolve_query_source(inline=None, file_path=query, stdin=None)

    assert result == query


def test_is_update_query_detects_update_keywords():
    from sparql.core.query_source import is_update_query

    assert is_update_query("INSERT DATA { ... }") is True
    assert is_update_query("DELETE WHERE { ... }") is True
    assert is_update_query("LOAD <http://ex.org/data>") is True
    assert is_update_query("CLEAR GRAPH <http://ex.org/g>") is True
    assert is_update_query("DROP ALL") is True
    assert is_update_query("SELECT ?s WHERE { ?s ?p ?o }") is False
    assert is_update_query("ASK { ?s ?p ?o }") is False


def test_is_update_query_handles_prefix_before_update():
    from sparql.core.query_source import is_update_query

    query = "PREFIX ex: <http://ex.org/> INSERT DATA { ex:s ex:p 'val' }"
    assert is_update_query(query) is True
