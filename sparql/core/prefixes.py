"""URI prefix resolution for readable output."""


class PrefixResolver:
    """Resolves URIs to prefixed names using configured namespace mappings.

    Matches longest namespace first to handle overlapping prefixes correctly
    (e.g., dcterms vs dc).
    """

    def __init__(self, prefixes: dict[str, str]) -> None:
        self.prefixes = prefixes
        # Sort by namespace length descending for longest-match-first
        self._sorted_prefixes = sorted(
            prefixes.items(),
            key=lambda x: len(x[1]),
            reverse=True,
        )

    def abbreviate(self, uri: str) -> str:
        for prefix, namespace in self._sorted_prefixes:
            if uri.startswith(namespace):
                return f"{prefix}:{uri[len(namespace):]}"
        return uri

    def expand(self, prefixed: str) -> str:
        """Expand prefixed name (prefix:local) to full URI.

        Returns the input unchanged if not a valid prefixed name or prefix unknown.
        """
        if ":" not in prefixed or prefixed.startswith("http"):
            return prefixed
        prefix, local = prefixed.split(":", 1)
        if prefix in self.prefixes:
            return f"{self.prefixes[prefix]}{local}"
        return prefixed

    def abbreviate_line(self, line: str) -> str:
        """Replace all namespace URIs in a line with their prefixed forms."""
        result = line
        for prefix, namespace in self._sorted_prefixes:
            result = result.replace(namespace, f"{prefix}:")
        return result


STANDARD_PREFIXES: dict[str, str] = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
    "foaf": "http://xmlns.com/foaf/0.1/",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "schema": "http://schema.org/",
    "dbo": "http://dbpedia.org/ontology/",
    "dbr": "http://dbpedia.org/resource/",
    "wd": "http://www.wikidata.org/entity/",
    "wdt": "http://www.wikidata.org/prop/direct/",
    "wikibase": "http://wikiba.se/ontology#",
}
