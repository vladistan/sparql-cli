"""Tests for SPARQL client (Step 2.2)."""

from unittest.mock import MagicMock

import httpx
import pytest

from sparql.core.client import SPARQLClient, _is_rdf_query
from sparql.core.exceptions import NetworkError
from sparql.core.exceptions import TimeoutError as SPARQLTimeoutError
from sparql.core.models import BindingValue, QueryResult, UpdateResult

# Wikidata requires descriptive User-Agent per their robot policy
# See: https://w.wiki/4wJS
WIKIDATA_USER_AGENT = (
    "sparql-cli/1.0 (https://github.com/vladistan/sparql-cli; test suite)"
)


@pytest.mark.integration
def test_client_executes_query_against_wikidata():
    client = SPARQLClient(
        endpoint_url="https://query.wikidata.org/sparql",
        timeout=30.0,
        user_agent=WIKIDATA_USER_AGENT,
    )

    query = "SELECT * WHERE { ?s ?p ?o } LIMIT 5"
    results = list(client.execute(query))

    assert len(results) == 5
    assert len(results[0].bindings) > 0


@pytest.mark.integration
def test_client_returns_iterator_of_query_result():
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
    client = SPARQLClient(
        endpoint_url="https://query.wikidata.org/sparql",
        timeout=0.001,  # Unrealistically short timeout
        user_agent=WIKIDATA_USER_AGENT,
    )

    query = "SELECT * WHERE { ?s ?p ?o } LIMIT 1"

    with pytest.raises(SPARQLTimeoutError):
        list(client.execute(query))


def test_client_handles_connection_error():
    client = SPARQLClient(
        endpoint_url="http://this-endpoint-does-not-exist-12345.invalid/sparql",
        timeout=5.0,
        user_agent="sparql-cli/1.0 (test)",
    )

    with pytest.raises(NetworkError):
        list(client.execute("SELECT * WHERE { ?s ?p ?o }"))


def test_is_rdf_query_detects_construct():
    assert _is_rdf_query("CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }")
    assert _is_rdf_query("construct { ?s ?p ?o } where { ?s ?p ?o }")
    assert _is_rdf_query(
        "PREFIX ex: <http://example.org/> CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }"
    )


def test_is_rdf_query_detects_describe():
    assert _is_rdf_query("DESCRIBE <http://example.org/resource>")
    assert _is_rdf_query("describe <http://example.org/resource>")
    assert _is_rdf_query(
        "PREFIX ex: <http://example.org/> DESCRIBE ex:resource"
    )


def test_is_rdf_query_rejects_select():
    assert not _is_rdf_query("SELECT * WHERE { ?s ?p ?o }")
    assert not _is_rdf_query("select * where { ?s ?p ?o }")


def test_is_rdf_query_rejects_ask():
    assert not _is_rdf_query("ASK { ?s ?p ?o }")
    assert not _is_rdf_query("ask { ?s ?p ?o }")


def test_execute_parses_ask_true_response(monkeypatch):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"head": {}, "boolean": True}

    _mock_httpx_client(monkeypatch, mock_response)

    client = SPARQLClient(
        endpoint_url="https://example.com/sparql",
        timeout=30.0,
        user_agent="test-agent/1.0",
    )

    results = list(client.execute("ASK { ?s ?p ?o }"))

    assert len(results) == 1
    assert results[0].bindings["boolean"].value == "true"
    assert results[0].variables == ["boolean"]


def test_execute_parses_ask_false_response(monkeypatch):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"head": {}, "boolean": False}

    _mock_httpx_client(monkeypatch, mock_response)

    client = SPARQLClient(
        endpoint_url="https://example.com/sparql",
        timeout=30.0,
        user_agent="test-agent/1.0",
    )

    results = list(client.execute("ASK { ?s ?p ?o }"))

    assert len(results) == 1
    assert results[0].bindings["boolean"].value == "false"
    assert results[0].variables == ["boolean"]


@pytest.mark.integration
def test_execute_rdf_returns_turtle():
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


def test_client_defaults_to_post():
    client = SPARQLClient(
        endpoint_url="https://example.com/sparql",
        timeout=30.0,
        user_agent="test-agent/1.0",
    )

    assert client.http_method == "POST"


def test_client_accepts_get_method():
    client = SPARQLClient(
        endpoint_url="https://example.com/sparql",
        timeout=30.0,
        user_agent="test-agent/1.0",
        http_method="GET",
    )

    assert client.http_method == "GET"


@pytest.mark.integration
def test_client_get_queries_dbpedia_successfully():
    """DBpedia (Virtuoso) requires GET — verify it works."""
    client = SPARQLClient(
        endpoint_url="https://dbpedia.org/sparql",
        timeout=30.0,
        user_agent="sparql-cli/test (testing HTTP GET support)",
        http_method="GET",
    )

    query = "SELECT ?p ?o WHERE { <http://dbpedia.org/resource/Anger> ?p ?o } LIMIT 5"
    results = list(client.execute(query))

    assert len(results) == 5
    assert len(results[0].bindings) > 0


@pytest.mark.integration
def test_client_post_fails_on_dbpedia():
    """DBpedia (Virtuoso) rejects POST with 405 — verify the bug scenario."""
    client = SPARQLClient(
        endpoint_url="https://dbpedia.org/sparql",
        timeout=30.0,
        user_agent="sparql-cli/test (testing HTTP POST rejection)",
        http_method="POST",
    )

    query = "SELECT ?p ?o WHERE { <http://dbpedia.org/resource/Anger> ?p ?o } LIMIT 5"
    with pytest.raises(NetworkError, match="HTTP 405"):
        list(client.execute(query))


@pytest.mark.integration
def test_client_post_works_on_wikidata():
    """Wikidata accepts POST (default) — verify existing behavior preserved."""
    client = SPARQLClient(
        endpoint_url="https://query.wikidata.org/sparql",
        timeout=30.0,
        user_agent=WIKIDATA_USER_AGENT,
        http_method="POST",
    )

    query = "SELECT * WHERE { ?s ?p ?o } LIMIT 3"
    results = list(client.execute(query))

    assert len(results) == 3
    assert len(results[0].bindings) > 0


def _mock_httpx_client(monkeypatch, mock_response):
    """Set up a mock httpx.Client that returns the given response."""
    mock_client_instance = MagicMock()
    mock_client_instance.__enter__ = MagicMock(
        return_value=mock_client_instance
    )
    mock_client_instance.__exit__ = MagicMock(return_value=False)
    mock_client_instance.post.return_value = mock_response

    monkeypatch.setattr(
        httpx, "Client", MagicMock(return_value=mock_client_instance)
    )
    return mock_client_instance


def test_execute_update_returns_update_result_on_success(monkeypatch):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "Update OK"
    mock_response.raise_for_status = MagicMock()

    _mock_httpx_client(monkeypatch, mock_response)

    client = SPARQLClient(
        endpoint_url="https://example.com/sparql/query",
        timeout=30.0,
        user_agent="test-agent/1.0",
    )

    result = client.execute_update(
        "INSERT DATA { <http://ex.org/s> <http://ex.org/p> 'val' }",
        update_endpoint="https://example.com/sparql/update",
    )

    assert isinstance(result, UpdateResult)
    assert result.success is True
    assert result.status_code == 200
    assert result.message == "Update OK"


def test_execute_update_sends_correct_content_type(monkeypatch):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "OK"
    mock_response.raise_for_status = MagicMock()

    mock_client = _mock_httpx_client(monkeypatch, mock_response)

    client = SPARQLClient(
        endpoint_url="https://example.com/sparql",
        timeout=30.0,
        user_agent="test-agent/1.0",
    )

    client.execute_update(
        "INSERT DATA { <http://ex.org/s> <http://ex.org/p> 'val' }",
        update_endpoint="https://example.com/sparql/update",
    )

    _, kwargs = mock_client.post.call_args
    assert kwargs["headers"]["Content-Type"] == "application/sparql-update"


def test_execute_update_sends_to_update_endpoint(monkeypatch):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "OK"
    mock_response.raise_for_status = MagicMock()

    mock_client = _mock_httpx_client(monkeypatch, mock_response)

    client = SPARQLClient(
        endpoint_url="https://example.com/sparql/query",
        timeout=30.0,
        user_agent="test-agent/1.0",
    )

    client.execute_update(
        "DELETE WHERE { ?s ?p ?o }",
        update_endpoint="https://example.com/sparql/update",
    )

    args, _ = mock_client.post.call_args
    assert args[0] == "https://example.com/sparql/update"


def test_execute_update_returns_failure_on_http_error(monkeypatch):
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Bad SPARQL syntax"
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "400", request=MagicMock(), response=mock_response,
    )

    _mock_httpx_client(monkeypatch, mock_response)

    client = SPARQLClient(
        endpoint_url="https://example.com/sparql",
        timeout=30.0,
        user_agent="test-agent/1.0",
    )

    result = client.execute_update(
        "INVALID UPDATE",
        update_endpoint="https://example.com/sparql/update",
    )

    assert result.success is False
    assert result.status_code == 400
    assert "Bad SPARQL syntax" in result.message


def test_execute_update_raises_on_timeout(monkeypatch):
    mock_client_instance = MagicMock()
    mock_client_instance.__enter__ = MagicMock(
        return_value=mock_client_instance
    )
    mock_client_instance.__exit__ = MagicMock(return_value=False)
    mock_client_instance.post.side_effect = httpx.TimeoutException("timeout")
    monkeypatch.setattr(
        httpx, "Client", MagicMock(return_value=mock_client_instance)
    )

    client = SPARQLClient(
        endpoint_url="https://example.com/sparql",
        timeout=30.0,
        user_agent="test-agent/1.0",
    )

    with pytest.raises(SPARQLTimeoutError):
        client.execute_update(
            "INSERT DATA { <http://ex.org/s> <http://ex.org/p> 'val' }",
            update_endpoint="https://example.com/sparql/update",
        )


def test_execute_update_raises_on_connection_error(monkeypatch):
    mock_client_instance = MagicMock()
    mock_client_instance.__enter__ = MagicMock(
        return_value=mock_client_instance
    )
    mock_client_instance.__exit__ = MagicMock(return_value=False)
    mock_client_instance.post.side_effect = httpx.ConnectError("failed")
    monkeypatch.setattr(
        httpx, "Client", MagicMock(return_value=mock_client_instance)
    )

    client = SPARQLClient(
        endpoint_url="https://example.com/sparql",
        timeout=30.0,
        user_agent="test-agent/1.0",
    )

    with pytest.raises(NetworkError):
        client.execute_update(
            "INSERT DATA { <http://ex.org/s> <http://ex.org/p> 'val' }",
            update_endpoint="https://example.com/sparql/update",
        )
