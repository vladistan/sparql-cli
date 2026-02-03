from sparql.core.monitoring import setup_sentry


def test_setup_monitoring_does_not_crash():
    setup_sentry()
