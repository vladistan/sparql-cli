# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.2] - 2026-07-12
### Fixed
- Honor the global `-G`/`--graph` filter in the `query` command. It was previously silently ignored (only the convenience commands applied it); now the raw `query` command scopes results to the named graph via the SPARQL 1.1 `default-graph-uri` protocol parameter.

## [0.2.1] - 2026-03-23
### Fixed
- Restore config.example.toml (only public endpoints).

## [0.2.0] - 2026-03-23
### Changed
- Renamed the package from `sparql-cli` to `sparql-tool`.

## [0.1.4] - 2026-02-24
### Fixed
- ASK query boolean handling.
### Added
- Test improvements; .gitignore.

## [0.1.3] - 2026-02-08
### Added
- SPARQL UPDATE support (INSERT, DELETE, LOAD, CLEAR, DROP).
### Fixed
- HTTP GET method handling.

## [0.1.2] - 2026-02-05
### Added
- CONSTRUCT/DESCRIBE support; RDF format validation.
### Fixed
- structlog logger configuration; sentry_sdk deprecation.

## [0.1.1] - 2026-02-04
### Fixed
- Global `--profile` and `--endpoint` options in the query command.

## [0.1.0] - 2026-02-03
### Added
- Initial public release.
