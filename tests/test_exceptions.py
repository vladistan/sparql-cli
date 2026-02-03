import pytest

from sparql.core.exceptions import (
    ConfigError,
    NetworkError,
    QueryError,
    QuerySyntaxError,
    SPARQLError,
    TimeoutError,
)
from sparql.core.exit_codes import ExitCode

# SPARQLError base tests

def test_sparql_error_is_exception():
    assert issubclass(SPARQLError, Exception)


def test_sparql_error_has_message():
    error = SPARQLError("Test error message")
    assert str(error) == "Test error message"


def test_sparql_error_has_exit_code():
    error = SPARQLError("Test error")
    assert hasattr(error, "exit_code")
    assert error.exit_code == ExitCode.GENERAL_ERROR


def test_sparql_error_default_exit_code():
    assert SPARQLError.exit_code == ExitCode.GENERAL_ERROR


# QueryError tests

def test_query_error_inherits_from_sparql_error():
    assert issubclass(QueryError, SPARQLError)


def test_query_error_exit_code():
    error = QueryError("Invalid query")
    assert error.exit_code == ExitCode.GENERAL_ERROR


def test_query_syntax_error_inherits_from_query_error():
    assert issubclass(QuerySyntaxError, QueryError)


def test_query_syntax_error_exit_code():
    error = QuerySyntaxError("Syntax error at line 1")
    assert error.exit_code == ExitCode.INPUT_ERROR


# NetworkError tests

def test_network_error_inherits_from_sparql_error():
    assert issubclass(NetworkError, SPARQLError)


def test_network_error_exit_code():
    error = NetworkError("Connection refused")
    assert error.exit_code == ExitCode.NETWORK_ERROR


def test_timeout_error_inherits_from_network_error():
    assert issubclass(TimeoutError, NetworkError)


def test_timeout_error_exit_code():
    error = TimeoutError("Request timed out after 30s")
    assert error.exit_code == ExitCode.TIMEOUT


# ConfigError tests

def test_config_error_inherits_from_sparql_error():
    assert issubclass(ConfigError, SPARQLError)


def test_config_error_exit_code():
    error = ConfigError("Invalid configuration")
    assert error.exit_code == ExitCode.INPUT_ERROR


# Exception catching tests

def test_catch_query_error_as_sparql_error():
    with pytest.raises(SPARQLError):
        raise QueryError("Test")


def test_catch_network_error_as_sparql_error():
    with pytest.raises(SPARQLError):
        raise NetworkError("Test")


def test_catch_config_error_as_sparql_error():
    with pytest.raises(SPARQLError):
        raise ConfigError("Test")


def test_catch_timeout_as_network_error():
    with pytest.raises(NetworkError):
        raise TimeoutError("Test")


def test_catch_query_syntax_as_query_error():
    with pytest.raises(QueryError):
        raise QuerySyntaxError("Test")
