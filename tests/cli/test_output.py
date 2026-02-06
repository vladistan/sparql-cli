"""Tests for output format definitions."""


def test_output_format_enum_has_rdf_formats():
    from sparql.cli.output import OutputFormat

    assert OutputFormat.turtle == "turtle"
    assert OutputFormat.ntriples == "ntriples"
    assert OutputFormat.nquads == "nquads"
    assert OutputFormat.rdfxml == "rdfxml"
    assert OutputFormat.jsonld == "jsonld"
    assert OutputFormat.trig == "trig"


def test_rdf_format_accept_headers_map():
    from sparql.cli.output import RDF_FORMAT_ACCEPT_HEADERS, OutputFormat

    assert RDF_FORMAT_ACCEPT_HEADERS[OutputFormat.turtle] == "text/turtle"
    assert RDF_FORMAT_ACCEPT_HEADERS[OutputFormat.ntriples] == "application/n-triples"
    assert RDF_FORMAT_ACCEPT_HEADERS[OutputFormat.nquads] == "application/n-quads"
    assert RDF_FORMAT_ACCEPT_HEADERS[OutputFormat.rdfxml] == "application/rdf+xml"
    assert RDF_FORMAT_ACCEPT_HEADERS[OutputFormat.jsonld] == "application/ld+json"
    assert RDF_FORMAT_ACCEPT_HEADERS[OutputFormat.trig] == "application/trig"


def test_rdf_format_accept_headers_only_contains_rdf_formats():
    from sparql.cli.output import RDF_FORMAT_ACCEPT_HEADERS, OutputFormat

    # Should only contain RDF formats, not tabular formats
    assert OutputFormat.json not in RDF_FORMAT_ACCEPT_HEADERS
    assert OutputFormat.csv not in RDF_FORMAT_ACCEPT_HEADERS
    assert OutputFormat.tsv not in RDF_FORMAT_ACCEPT_HEADERS
    assert OutputFormat.table not in RDF_FORMAT_ACCEPT_HEADERS
