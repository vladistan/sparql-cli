def test_package_imports_without_errors():
    import sparql

    assert sparql is not None


def test_version_is_accessible():
    import sparql

    assert hasattr(sparql, "__version__")
    assert isinstance(sparql.__version__, str)
    assert len(sparql.__version__) > 0


def test_version_format():
    import sparql

    parts = sparql.__version__.split(".")
    assert len(parts) >= 2, "Version should have at least major.minor"
    assert parts[0].isdigit(), "Major version should be numeric"
    assert parts[1].isdigit(), "Minor version should be numeric"


def test_core_subpackage_imports():
    from sparql import core

    assert core is not None


def test_cli_subpackage_imports():
    from sparql import cli

    assert cli is not None


def test_formatters_subpackage_imports():
    from sparql import formatters

    assert formatters is not None
