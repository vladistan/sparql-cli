from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

# Public SPARQL endpoint for integration tests
WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"


@pytest.fixture
def wikidata_endpoint():
    """Public Wikidata SPARQL endpoint for integration tests."""
    return WIKIDATA_ENDPOINT


@pytest.fixture
def sample_sparql_query():
    return "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10"


@pytest.fixture
def temp_dir():
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_query_file(temp_dir, sample_sparql_query):
    query_file = temp_dir / "query.sparql"
    query_file.write_text(sample_sparql_query)
    return query_file
