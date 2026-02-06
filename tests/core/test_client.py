"""Tests for SPARQL client (Step 2.2)."""

import pytest

# Wikidata requires descriptive User-Agent per their robot policy
# See: https://w.wiki/4wJS
WIKIDATA_USER_AGENT = (
    "sparql-cli/1.0 (https://github.com/vladistan/sparql-cli; test suite)"
)


# Integration tests against real endpoint
@pytest.mark.integration
def test_client_executes_query_against_wikidata():
    from sparql.core.client import SPARQLClient

    client = SPARQLClient(
        endpoint_url="https://query.wikidata.org/sparql",
        timeout=30.0,
        user_agent=WIKIDATA_USER_AGENT,
    )

    query = "SELECT * WHERE { ?s ?p ?o } LIMIT 5"
    results = list(client.execute(query))

    assert len(results) == 5
    assert results[0].bindings


@pytest.mark.integration
def test_client_returns_iterator_of_query_result():
    from sparql.core.client import SPARQLClient
    from sparql.core.models import QueryResult

    client = SPARQLClient(
        endpoint_url="https://query.wikidata.org/sparql",
        timeout=30.0,
        user_agent=WIKIDATA_USER_AGENT,
    )

    query = "SELECT ?item WHERE { ?item wdt:P31 wd:Q5 } LIMIT 3"
    results = client.execute(query)

    # Should be an iterator, not a list
    first = next(results)
    assert isinstance(first, QueryResult)
    assert "item" in first.bindings


@pytest.mark.integration
def test_client_parses_sparql_json_results():
    from sparql.core.client import SPARQLClient
    from sparql.core.models import BindingValue

    client = SPARQLClient(
        endpoint_url="https://query.wikidata.org/sparql",
        timeout=30.0,
        user_agent=WIKIDATA_USER_AGENT,
    )

    # Simple query without SERVICE clause for faster execution
    query = "SELECT ?s ?p WHERE { ?s ?p wd:Q42 } LIMIT 1"
    results = list(client.execute(query))

    assert len(results) == 1
    result = results[0]
    assert "s" in result.bindings
    assert isinstance(result.bindings["s"], BindingValue)
    assert result.bindings["s"].type == "uri"


@pytest.mark.integration
def test_client_handles_http_error():
    from sparql.core.client import SPARQLClient
    from sparql.core.exceptions import NetworkError

    client = SPARQLClient(
        endpoint_url="https://query.wikidata.org/sparql",
        timeout=30.0,
        user_agent=WIKIDATA_USER_AGENT,
    )

    # Invalid SPARQL syntax should return HTTP 400
    query = "THIS IS NOT VALID SPARQL"

    with pytest.raises(NetworkError):
        list(client.execute(query))


@pytest.mark.integration
def test_client_handles_timeout():
    from sparql.core.client import SPARQLClient
    from sparql.core.exceptions import TimeoutError

    client = SPARQLClient(
        endpoint_url="https://query.wikidata.org/sparql",
        timeout=0.001,  # Unrealistically short timeout
        user_agent=WIKIDATA_USER_AGENT,
    )

    query = "SELECT * WHERE { ?s ?p ?o } LIMIT 1"

    with pytest.raises(TimeoutError):
        list(client.execute(query))


def test_client_handles_connection_error():
    from sparql.core.client import SPARQLClient
    from sparql.core.exceptions import NetworkError

    client = SPARQLClient(
        endpoint_url="http://this-endpoint-does-not-exist-12345.invalid/sparql",
        timeout=5.0,
        user_agent="sparql-cli/1.0 (test)",
    )

    with pytest.raises(NetworkError):
        list(client.execute("SELECT * WHERE { ?s ?p ?o }"))


def test_is_rdf_query_detects_construct():
    from sparql.core.client import _is_rdf_query

    assert _is_rdf_query("CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }")
    assert _is_rdf_query("construct { ?s ?p ?o } where { ?s ?p ?o }")
    assert _is_rdf_query(
        "PREFIX ex: <http://example.org/> CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }"
    )


def test_is_rdf_query_detects_describe():
    from sparql.core.client import _is_rdf_query

    assert _is_rdf_query("DESCRIBE <http://example.org/resource>")
    assert _is_rdf_query("describe <http://example.org/resource>")
    assert _is_rdf_query(
        "PREFIX ex: <http://example.org/> DESCRIBE ex:resource"
    )


def test_is_rdf_query_rejects_select():
    from sparql.core.client import _is_rdf_query

    assert not _is_rdf_query("SELECT * WHERE { ?s ?p ?o }")
    assert not _is_rdf_query("select * where { ?s ?p ?o }")


def test_is_rdf_query_rejects_ask():
    from sparql.core.client import _is_rdf_query

    assert not _is_rdf_query("ASK { ?s ?p ?o }")
    assert not _is_rdf_query("ask { ?s ?p ?o }")


@pytest.mark.integration
def test_execute_rdf_returns_turtle():
    from sparql.core.client import SPARQLClient

    client = SPARQLClient(
        endpoint_url="https://query.wikidata.org/sparql",
        timeout=30.0,
        user_agent=WIKIDATA_USER_AGENT,
    )

    query = (
        "CONSTRUCT { <http://example.org/s> <http://example.org/p>"
        " <http://example.org/o> } WHERE { BIND(1 AS ?x) }"
    )
    rdf_response = client.execute_rdf(query, "text/turtle")

    assert isinstance(rdf_response, str)
    assert len(rdf_response) > 0
    # Turtle format should contain at least one triple or prefix
    assert "<http://example.org/" in rdf_response or "@prefix" in rdf_response


@pytest.mark.integration
def test_execute_rdf_returns_ntriples():
    from sparql.core.client import SPARQLClient

    client = SPARQLClient(
        endpoint_url="https://query.wikidata.org/sparql",
        timeout=30.0,
        user_agent=WIKIDATA_USER_AGENT,
    )

    query = (
        "CONSTRUCT { <http://example.org/s> <http://example.org/p>"
        " <http://example.org/o> } WHERE { BIND(1 AS ?x) }"
    )
    rdf_response = client.execute_rdf(query, "application/n-triples")

    assert isinstance(rdf_response, str)
    assert len(rdf_response) > 0
    # N-Triples format uses full URIs
    assert "<http://example.org/" in rdf_response
