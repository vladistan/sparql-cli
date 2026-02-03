"""Tests for URI prefix resolution."""

import pytest

from sparql.core.prefixes import STANDARD_PREFIXES, PrefixResolver


def test_abbreviate_known_prefix():
    resolver = PrefixResolver({"rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#"})

    result = resolver.abbreviate("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")

    assert result == "rdf:type"


def test_abbreviate_unknown_prefix_returns_original():
    resolver = PrefixResolver({"rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#"})

    result = resolver.abbreviate("http://unknown.org/property")

    assert result == "http://unknown.org/property"


def test_abbreviate_empty_local_name():
    resolver = PrefixResolver({"schema": "http://schema.org/"})

    result = resolver.abbreviate("http://schema.org/")

    assert result == "schema:"


def test_abbreviate_longest_match_first():
    # dcterms should match before dc since it's longer
    resolver = PrefixResolver({
        "dc": "http://purl.org/dc/elements/1.1/",
        "dcterms": "http://purl.org/dc/terms/",
    })

    result = resolver.abbreviate("http://purl.org/dc/terms/title")

    assert result == "dcterms:title"


def test_abbreviate_line_replaces_all_uris():
    resolver = PrefixResolver({
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    })
    line = '{"p": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type", "o": "http://www.w3.org/2000/01/rdf-schema#Class"}'

    result = resolver.abbreviate_line(line)

    assert result == '{"p": "rdf:type", "o": "rdfs:Class"}'


def test_abbreviate_line_preserves_non_uri_content():
    resolver = PrefixResolver({"rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#"})
    line = "Some text without any URIs"

    result = resolver.abbreviate_line(line)

    assert result == "Some text without any URIs"


def test_standard_prefixes_contains_common_namespaces():
    assert "rdf" in STANDARD_PREFIXES
    assert "rdfs" in STANDARD_PREFIXES
    assert "owl" in STANDARD_PREFIXES
    assert "xsd" in STANDARD_PREFIXES
    assert "dc" in STANDARD_PREFIXES
    assert "dcterms" in STANDARD_PREFIXES
    assert "foaf" in STANDARD_PREFIXES
    assert "skos" in STANDARD_PREFIXES
    assert "schema" in STANDARD_PREFIXES
    assert "wd" in STANDARD_PREFIXES
    assert "wdt" in STANDARD_PREFIXES
    assert "wikibase" in STANDARD_PREFIXES


def test_standard_prefixes_values_are_valid_uris():
    for prefix, namespace in STANDARD_PREFIXES.items():
        assert namespace.startswith("http://") or namespace.startswith("https://"), (
            f"Prefix {prefix} has invalid namespace: {namespace}"
        )


@pytest.mark.parametrize("prefix,namespace,uri,expected", [
    (
        "rdf",
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        "rdf:type",
    ),
    (
        "wd",
        "http://www.wikidata.org/entity/",
        "http://www.wikidata.org/entity/Q42",
        "wd:Q42",
    ),
    (
        "wdt",
        "http://www.wikidata.org/prop/direct/",
        "http://www.wikidata.org/prop/direct/P31",
        "wdt:P31",
    ),
    (
        "schema",
        "http://schema.org/",
        "http://schema.org/Person",
        "schema:Person",
    ),
])
def test_abbreviate_various_prefixes(prefix, namespace, uri, expected):
    resolver = PrefixResolver({prefix: namespace})

    result = resolver.abbreviate(uri)

    assert result == expected
