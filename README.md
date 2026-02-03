# SPARQL CLI

CLI tool for querying SPARQL endpoints from the command line.

## Installation

### From PyPI (recommended)

```bash
pip install sparql-cli
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv tool install sparql-cli
```

### From Source

```bash
git clone https://github.com/vlad/sparql-cli.git
cd sparql-cli
uv sync --dev
```

## Quick Start

### Query Public Endpoints

```bash
# Planet names across cultures - English, Welsh, Ukrainian, Chinese, Arabic, Latin (Wikidata)
sparql query -P wikidata -e "SELECT ?en ?cy ?uk ?zh ?ar ?la WHERE {
  VALUES ?planet { wd:Q308 wd:Q313 wd:Q2 wd:Q111 wd:Q319 wd:Q193 wd:Q324 wd:Q332 }
  OPTIONAL { ?planet rdfs:label ?en FILTER(LANG(?en) = 'en') }
  OPTIONAL { ?planet rdfs:label ?cy FILTER(LANG(?cy) = 'cy') }
  OPTIONAL { ?planet rdfs:label ?uk FILTER(LANG(?uk) = 'uk') }
  OPTIONAL { ?planet rdfs:label ?zh FILTER(LANG(?zh) = 'zh') }
  OPTIONAL { ?planet rdfs:label ?ar FILTER(LANG(?ar) = 'ar') }
  OPTIONAL { ?planet rdfs:label ?la FILTER(LANG(?la) = 'la') }
}" --table

# Find scientists (DBpedia)
sparql query -P dbpedia -e "SELECT DISTINCT ?person ?name WHERE {
  ?person a dbo:Scientist; foaf:name ?name.
  FILTER(lang(?name)='en')
} LIMIT 5"

# Protein counts for model organisms - Human, Mouse, Fly, Worm, Yeast, Plant (UniProt)
sparql query -P uniprot -e "PREFIX up: <http://purl.uniprot.org/core/>
PREFIX taxon: <http://purl.uniprot.org/taxonomy/>
SELECT ?organism (COUNT(?protein) AS ?proteins) WHERE {
  VALUES ?tax { taxon:9606 taxon:10090 taxon:7227 taxon:6239 taxon:4932 taxon:3702 }
  ?protein a up:Protein ; up:organism ?tax .
  ?tax up:scientificName ?organism .
} GROUP BY ?organism ORDER BY DESC(?proteins)"

# Approved drugs with most known targets - generic name, brand, target count (ChEMBL)
echo 'PREFIX chembl: <http://rdf.ebi.ac.uk/terms/chembl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?generic (SAMPLE(?brand) AS ?brandName) (COUNT(DISTINCT ?target) AS ?targets) WHERE {
  ?mol a chembl:SmallMolecule ; rdfs:label ?generic ; chembl:highestDevelopmentPhase 4 ;
       skos:altLabel ?brand ; chembl:hasActivity/chembl:hasAssay/chembl:hasTarget ?target .
  FILTER(REGEX(?brand, "^[A-Z][a-z]+$"))
  FILTER(!REGEX(?brand, ?generic, "i"))
} GROUP BY ?generic ORDER BY DESC(?targets) LIMIT 10' | sparql query -E "https://chemblmirror.rdf.bigcat-bioinformatics.org/sparql" -t 120

# Simple query from file
sparql query query.rq
```

### Explore Endpoints with Convenience Commands

```bash
# List classes in an endpoint
sparql classes -P dbpedia -n 10

# List predicates
sparql predicates -P wikidata -n 10

# Explore a specific entity (Douglas Adams = Q42)
sparql explore wd:Q42 -P wikidata -n 5

# List instances of a class
sparql objects dbo:Scientist -P dbpedia -n 5

# Describe a specific resource
sparql object dbr:Albert_Einstein -P dbpedia
```

### Override Endpoint

```bash
# Use a different profile
sparql query --profile dbpedia -e "SELECT * WHERE { ?s ?p ?o } LIMIT 5"

# Override endpoint URL directly
sparql query --endpoint https://example.com/sparql -e "SELECT * WHERE { ?s ?p ?o } LIMIT 5"
```

## Commands

### `query` - Execute SPARQL Queries

Execute arbitrary SPARQL queries against an endpoint.

```bash
sparql query -e "SELECT * WHERE { ?s ?p ?o } LIMIT 5"
sparql query query.rq
cat query.rq | sparql query
```

### `classes` - List RDF Classes

List distinct `rdf:type` values in the endpoint.

```bash
sparql classes -P wikidata -n 20
sparql classes --labels  # Include rdfs:label (slower)
```

### `predicates` - List Predicates

List distinct predicates, or show usage of a specific predicate.

```bash
sparql predicates -P dbpedia -n 20
sparql predicates rdf:type --values  # Show distinct values
```

### `explore` - Explore URI Relationships

Find all triples where a URI appears as subject, predicate, or object.

```bash
sparql explore wd:Q42 -P wikidata
sparql explore dbo:Person -P dbpedia
```

### `objects` - List Class Instances

List instances of a given RDF class.

```bash
sparql objects dbo:Scientist -P dbpedia -n 10
sparql objects foaf:Person -P dbpedia --labels
```

### `object` - Describe Resource

Show all predicates and values for a specific resource.

```bash
sparql object dbr:Albert_Einstein -P dbpedia
sparql object wd:Q42 -P wikidata
```

### `graphs` - List Named Graphs

List named graphs in the endpoint.

```bash
sparql graphs -P dbpedia -n 10
```

### `config` - Configuration Management

```bash
sparql config show        # Show current configuration
sparql config show --json # Output as JSON
sparql config profiles    # List available profiles
```

## Global Options

These options work with all commands:

| Option | Short | Description |
|--------|-------|-------------|
| `--profile` | `-P` | Use named endpoint profile |
| `--endpoint` | `-E` | Override endpoint URL |
| `--graphs` | `-g` | Show graph column in output |
| `--graph` | `-G` | Filter to specific named graph |
| `--verbose` | | Enable verbose logging |
| `--version` | `-V` | Show version and exit |

## Command-Specific Options

### Query Options

| Option | Short | Description |
|--------|-------|-------------|
| `--execute` | `-e` | Inline SPARQL query |
| `--timeout` | `-t` | Query timeout in seconds |
| `--format` | `-f` | Output format (json, jsonl, table, csv, tsv, sparql11) |
| `--table` | | Shorthand for `--format table` |
| `--jsonl` | | Shorthand for `--format jsonl` |
| `--compact` | | No pretty-print for sparql11 |
| `--no-header` | | Skip header for CSV/TSV |
| `--width` | | Max column width for table |
| `--user` | `-u` | Username for auth |
| `--password` | `-p` | Password for auth |
| `--digest` | | Use HTTP Digest auth |

### Convenience Command Options

| Option | Short | Description |
|--------|-------|-------------|
| `--limit` | `-n` | Max results (default: 100) |
| `--labels` | `-l` | Include rdfs:label (slower) |
| `--values` | | Show only values (predicates cmd) |

## Output Formats

The CLI supports multiple output formats. By default, it auto-detects:
- **Interactive terminal**: Table format with colored headers
- **Piped output**: TSV format for easy processing

### Available Formats

| Format | Flag | Description |
|--------|------|-------------|
| `table` | `--format table` or `--table` | Rich formatted table with headers |
| `json` | `--format json` | JSON array of objects (pandas-compatible) |
| `jsonl` | `--format jsonl` or `--jsonl` | JSON Lines (one object per line, streaming) |
| `sparql11` | `--format sparql11` | SPARQL 1.1 Query Results JSON Format |
| `csv` | `--format csv` | RFC 4180 CSV with proper escaping |
| `tsv` | `--format tsv` | Tab-separated values |

### Format Examples

```bash
# Pretty table for interactive exploration
sparql query -e "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 5" --table

# JSON for loading into pandas
sparql query -e "SELECT ?item ?label WHERE { ... }" --format json > results.json

# JSONL for streaming pipelines
sparql query -e "SELECT * WHERE { ... }" --jsonl | jq '.item'

# TSV for spreadsheets or unix tools
sparql query -e "SELECT * WHERE { ... }" --format tsv | cut -f1

# Table with custom column width
sparql query -e "..." --table --width 60

# CSV/TSV without header row
sparql query -e "..." --format csv --no-header
```

## Configuration

Create `~/.config/sparql/config.toml`:

```toml
# Default profile to use
default_endpoint = "wikidata"

[endpoints.wikidata]
url = "https://query.wikidata.org/sparql"
timeout = 60.0

[endpoints.dbpedia]
url = "https://dbpedia.org/sparql"

# Private endpoint with authentication
[endpoints.private]
url = "https://private.example.com/sparql"
auth_type = "basic"  # or "digest"
username = "admin"
password = "secret" # pragma: allowlist secret
```

View current configuration:

```bash
sparql config show
sparql config show --json
sparql config profiles
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `SPARQL_PROFILE` | Override default profile |
| `SPARQL_ENDPOINT` | Override endpoint URL |
| `SPARQL_TIMEOUT` | Override timeout (seconds) |
| `SPARQL_USER` | Override username |
| `SPARQL_PASSWORD` | Override password |

### Precedence

CLI flags > Environment variables > Profile settings > Config defaults

## Authentication

Authentication can be configured per-profile in config file:

```toml
[endpoints.marklogic]
url = "http://localhost:8000/v1/graphs/sparql"
auth_type = "digest"
username = "admin"
password = "your-password" # pragma: allowlist secret
```

Or via CLI/environment:

```bash
# CLI flags
sparql query --user admin --password secret --digest -e "..."

# Environment
SPARQL_USER=admin SPARQL_PASSWORD=secret sparql query -e "..."
```

## Troubleshooting

### Debugging Options

```bash
# Show endpoint and query before execution
sparql classes -P dbpedia --verbose

# Show which graph data comes from
sparql classes -P dbpedia --graphs

# Filter to specific named graph
sparql classes -P dbpedia --graph http://dbpedia.org
```

### Common Issues

**Connection errors:**
```bash
# Check endpoint is reachable
sparql config show  # Verify endpoint URL
sparql query -E https://your-endpoint/sparql -e "SELECT * WHERE { ?s ?p ?o } LIMIT 1"
```

**Query timeout:**
```bash
# Increase timeout
sparql query -t 120 -e "..."  # 2 minute timeout
```

**Unknown profile:**
```bash
# List available profiles
sparql config profiles
```

**Empty results:**
- Check if the endpoint has data: `sparql classes -n 5`
- Verify predicates exist: `sparql predicates -n 5`
- Try with verbose mode: `--verbose`

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Usage error |
| 3 | Input error (bad query file, empty query) |
| 5 | Network error |
| 6 | Timeout |
| 7 | Config error |

## Endpoint Notes

| Server | URL Format |
|--------|------------|
| Stardog | Must end with `/query` (e.g., `http://host:5820/db-name/query`) |
| MarkLogic | Use `/v1/graphs/sparql` path |
| Blazegraph | Standard `/sparql` or `/blazegraph/sparql` |
| Fuseki | Use `/dataset/sparql` or `/dataset/query` |

## Development

```bash
git clone https://github.com/vlad/sparql-cli.git
cd sparql-cli
uv sync --dev

# Run tests
uv run pytest

# Type checking
uv run mypy sparql/

# Linting
uv run ruff check .
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Links

- **Repository**: https://github.com/vlad/sparql-cli
- **Issue Tracker**: https://github.com/vlad/sparql-cli/issues
- **PyPI**: https://pypi.org/project/sparql-cli/
