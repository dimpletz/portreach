"""Core port checking functionality."""

import math
import socket
from collections.abc import Sequence

from portreach.exceptions import (
    InvalidHostError,
    InvalidPortError,
    InvalidRangeError,
)
from portreach.models import CheckResult, PortResult


def _validate_timeout(timeout: float) -> None:
    try:
        valid_timeout = math.isfinite(timeout) and timeout > 0
    except (OverflowError, TypeError):
        valid_timeout = False

    if not valid_timeout:
        raise ValueError("timeout must be a finite positive number")

    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        probe.settimeout(timeout)
    except (OverflowError, TypeError, ValueError) as exc:
        raise ValueError("timeout is outside the supported platform range") from exc
    finally:
        probe.close()


def validate_port(port: int) -> None:
    """Validate that a port number is within valid range (1-65535).

    Args:
        port: The port number to validate.

    Raises:
        InvalidPortError: If port is not in valid range.
    """
    if not isinstance(port, int) or port < 1 or port > 65535:
        raise InvalidPortError(f"Port must be between 1 and 65535, got {port}")


def parse_ports(port_specs: Sequence[str]) -> list[int]:
    """Parse port specifications into a list of port numbers.

    Supports individual ports and ranges. Examples:
    - "80" -> [80]
    - "8000-8010" -> [8000, 8001, ..., 8010]

    Args:
        port_specs: Sequence of port specifications (strings).

    Returns:
        List of port numbers.

    Raises:
        InvalidPortError: If a port number is invalid.
        InvalidRangeError: If a range is malformed or invalid.
    """
    ports: list[int] = []

    for spec in port_specs:
        if "-" in spec:
            # Parse range
            parts = spec.split("-")
            if len(parts) != 2:
                raise InvalidRangeError(f"Invalid port range: {spec} (expected format: start-end)")

            try:
                start = int(parts[0].strip())
                end = int(parts[1].strip())
            except ValueError as exc:
                raise InvalidRangeError(
                    f"Invalid port range: {spec} (ports must be integers)"
                ) from exc

            validate_port(start)
            validate_port(end)

            if start > end:
                raise InvalidRangeError(f"Invalid port range: {spec} (start {start} > end {end})")

            ports.extend(range(start, end + 1))
        else:
            # Single port
            try:
                port = int(spec.strip())
            except ValueError as exc:
                raise InvalidPortError(f"Invalid port number: {spec}") from exc

            validate_port(port)
            ports.append(port)

    return ports


def _resolve_host_addresses(host: str) -> list[tuple[int, str]]:
    """Resolve a hostname to a list of (address_family, address) tuples.

    Args:
        host: Hostname or IP address.

    Returns:
        List of (socket.AF_INET or socket.AF_INET6, IP address) tuples.

    Raises:
        InvalidHostError: If hostname cannot be resolved.
    """
    try:
        # getaddrinfo returns: (family, type, proto, canonname, sockaddr)
        # We extract family and IP from each result
        result = socket.getaddrinfo(host, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        if not result:
            raise InvalidHostError(f"Could not resolve hostname '{host}'")

        # Build list of (family, address) tuples
        # sockaddr[0] is the IP address, result[i][0] is address family
        addresses: list[tuple[int, str]] = [(res[0], str(res[4][0])) for res in result]
        return addresses

    except socket.gaierror as e:
        raise InvalidHostError(f"Could not resolve hostname '{host}': {e}") from e
    except OSError as e:
        raise InvalidHostError(f"Error resolving hostname '{host}': {e}") from e


def check_port(host: str, port: int, timeout: float = 2.0) -> PortResult:
    """Check if a single TCP port is open on a host.

    Attempts connection to the host using each resolved address
    (IPv4 and/or IPv6). A successful connection to any resolved
    address means the port is open.

    Args:
        host: Hostname or IP address.
        port: Port number to check.
        timeout: Connection timeout in seconds (default: 2.0).

    Returns:
        PortResult with status "open" or "closed".
    """
    validate_port(port)
    _validate_timeout(timeout)

    return _check_port_validated(host, port, timeout)


def _check_port_validated(host: str, port: int, timeout: float) -> PortResult:
    try:
        addresses = _resolve_host_addresses(host)
    except InvalidHostError as e:
        return PortResult(
            port=port,
            status="closed",
            error=str(e),
        )

    # Try each resolved address
    for family, addr in addresses:
        try:
            sock = socket.socket(family, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            try:
                sock.connect((addr, port))
                # Successful connection
                return PortResult(port=port, status="open")
            finally:
                sock.close()
        except (TimeoutError, OSError):
            # This address failed, try the next one
            continue

    # All addresses failed to connect
    return PortResult(port=port, status="closed")


def check_ports(
    host: str,
    ports: Sequence[int],
    timeout: float = 2.0,
) -> CheckResult:
    """Check multiple TCP ports on a host.

    Args:
        host: Hostname or IP address.
        ports: List of port numbers to check.
        timeout: Connection timeout in seconds (default: 2.0).

    Returns:
        CheckResult with results for each port.
    """
    _validate_timeout(timeout)
    results = []
    for port in ports:
        validate_port(port)
        results.append(_check_port_validated(host, port, timeout))
    return CheckResult(host=host, results=results, timeout=timeout)
