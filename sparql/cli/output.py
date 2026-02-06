"""Shared output format definitions for CLI commands."""

from enum import Enum


class OutputFormat(str, Enum):
    json = "json"
    jsonl = "jsonl"
    sparql11 = "sparql11"
    table = "table"
    csv = "csv"
    tsv = "tsv"
    turtle = "turtle"
    ntriples = "ntriples"
    nquads = "nquads"
    rdfxml = "rdfxml"
    jsonld = "jsonld"
    trig = "trig"


# Accept headers for RDF serialization formats (CONSTRUCT/DESCRIBE queries)
RDF_FORMAT_ACCEPT_HEADERS = {
    OutputFormat.turtle: "text/turtle",
    OutputFormat.ntriples: "application/n-triples",
    OutputFormat.nquads: "application/n-quads",
    OutputFormat.rdfxml: "application/rdf+xml",
    OutputFormat.jsonld: "application/ld+json",
    OutputFormat.trig: "application/trig",
}
