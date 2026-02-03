"""Sentry integration for error tracking and performance monitoring.

Sentry is initialized early in main() after logging setup.
Initialization can be enabled via SPARQL_CLI_TELEMETRY_ENABLED environment variable.
"""

import os

import sentry_sdk

from sparql._version import __version__


def setup_sentry(environment: str = "local") -> None:
    """Initialize Sentry if telemetry is enabled via environment variable.

    Args:
        environment: Sentry environment tag (local, staging, production)

    Environment Variables:
        SPARQL_CLI_TELEMETRY_ENABLED: Set to "true" to enable. Default: disabled.
    """
    env_val = os.getenv("SPARQL_CLI_TELEMETRY_ENABLED", "false")
    telemetry_enabled = env_val.lower() == "true"

    if not telemetry_enabled:
        # Telemetry disabled via environment variable
        return

    sentry_sdk.init(
        dsn="https://662b8b54b981d2d875aa135277fc63f3@o4508594232426496.ingest.us.sentry.io/4510823620739072",
        traces_sample_rate=1.0,
        environment=environment,
        release=__version__,
        attach_stacktrace=True,
        send_default_pii=False,
    )
