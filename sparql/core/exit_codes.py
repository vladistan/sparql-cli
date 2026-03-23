"""Standard exit codes for SPARQL CLI.

Exit codes follow Unix conventions.
"""

from enum import IntEnum


class ExitCode(IntEnum):
    SUCCESS = 0
    GENERAL_ERROR = 1
    USAGE_ERROR = 2
    INPUT_ERROR = 3
    OUTPUT_ERROR = 4
    NETWORK_ERROR = 5
    TIMEOUT = 6
    CONFIG_ERROR = 7
