from sparql.core.logging import get_logger, setup_logging


def test_setup_logging_runs_without_error():
    setup_logging(verbose=False)


def test_setup_logging_verbose_mode():
    setup_logging(verbose=True)


def test_get_logger_returns_logger():
    setup_logging()
    logger = get_logger()
    assert logger is not None


def test_get_logger_with_name():
    setup_logging()
    logger = get_logger("test_module")
    assert logger is not None


def test_logger_can_log_message(capsys):
    """Verifies logs go to stderr for clean stdout piping."""
    setup_logging(verbose=True)
    logger = get_logger("test")
    logger.debug("test message")
    captured = capsys.readouterr()
    assert "test message" in captured.err
