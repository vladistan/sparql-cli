"""Exception hierarchy for SPARQL CLI.

Exit codes are defined in exit_codes.py and follow CODE-PY-CLI-001 pattern.
"""

from sparql.core.exit_codes import ExitCode


class SPARQLError(Exception):
    exit_code: int = ExitCode.GENERAL_ERROR

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class QueryError(SPARQLError):
    exit_code: int = ExitCode.GENERAL_ERROR


class QuerySyntaxError(QueryError):
    exit_code: int = ExitCode.INPUT_ERROR


class NetworkError(SPARQLError):
    exit_code: int = ExitCode.NETWORK_ERROR


class TimeoutError(NetworkError):
    exit_code: int = ExitCode.TIMEOUT


class ConfigError(SPARQLError):
    exit_code: int = ExitCode.INPUT_ERROR
