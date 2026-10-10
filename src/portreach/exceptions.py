"""Custom exceptions for PortReach."""


class PortReachError(Exception):
    """Base exception for PortReach."""


class InvalidHostError(PortReachError):
    """Raised when a hostname cannot be resolved or is invalid."""


class InvalidPortError(PortReachError):
    """Raised when a port number is invalid."""


class InvalidRangeError(PortReachError):
    """Raised when a port range is invalid."""
