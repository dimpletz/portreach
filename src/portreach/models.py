"""Data models for PortReach results."""

from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class PortResult:
    """Result of checking a single port.

    Attributes:
        port: The port number that was checked.
        status: Either "open" if the port is reachable, or "closed" if not.
        error: Optional error message if the check failed.
    """

    port: int
    status: Literal["open", "closed"]
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format for JSON serialization."""
        result: dict[str, Any] = {"port": self.port, "status": self.status}
        if self.error:
            result["error"] = self.error
        return result


@dataclass
class CheckResult:
    """Result of checking ports on a host.

    Attributes:
        host: The hostname or IP address that was checked.
        results: List of PortResult objects for each checked port.
        timeout: The timeout value used for checks.
    """

    host: str
    results: list[PortResult]
    timeout: float

    @property
    def all_open(self) -> bool:
        """Return True if all ports are open."""
        return all(r.status == "open" for r in self.results)

    @property
    def any_open(self) -> bool:
        """Return True if any port is open."""
        return any(r.status == "open" for r in self.results)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format for JSON serialization."""
        return {
            "host": self.host,
            "results": [r.to_dict() for r in self.results],
        }
