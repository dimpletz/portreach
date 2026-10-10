"""PortReach: A lightweight TCP connectivity diagnostic utility."""

__version__ = "0.1.0"
__author__ = "Ofelia B Webb"

from portreach.checker import check_port, check_ports
from portreach.exceptions import InvalidHostError, InvalidPortError, PortReachError
from portreach.models import CheckResult, PortResult

__all__ = [
    "check_port",
    "check_ports",
    "PortReachError",
    "InvalidHostError",
    "InvalidPortError",
    "PortResult",
    "CheckResult",
]
