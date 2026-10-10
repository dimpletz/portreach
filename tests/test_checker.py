"""Tests for port checking and validation."""

import socket

import pytest

from portreach.checker import (
    _resolve_host_addresses,
    check_port,
    check_ports,
    parse_ports,
    validate_port,
)
from portreach.exceptions import (
    InvalidHostError,
    InvalidPortError,
    InvalidRangeError,
)
from portreach.models import CheckResult, PortResult


class TestPortValidation:
    """Test port number validation."""

    def test_valid_port(self):
        """Valid port should not raise."""
        validate_port(80)
        validate_port(1)
        validate_port(65535)

    def test_invalid_port_too_low(self):
        """Port below 1 should raise InvalidPortError."""
        with pytest.raises(InvalidPortError):
            validate_port(0)

    def test_invalid_port_too_high(self):
        """Port above 65535 should raise InvalidPortError."""
        with pytest.raises(InvalidPortError):
            validate_port(65536)

    def test_invalid_port_not_int(self):
        """Non-integer port should raise InvalidPortError."""
        with pytest.raises(InvalidPortError):
            validate_port("80")  # type: ignore


class TestParsePortSpecs:
    """Test parsing of port specifications."""

    def test_single_port(self):
        """Single port should parse correctly."""
        assert parse_ports(["80"]) == [80]
        assert parse_ports(["443"]) == [443]

    def test_multiple_single_ports(self):
        """Multiple individual ports should parse correctly."""
        result = parse_ports(["80", "443", "8080"])
        assert result == [80, 443, 8080]

    def test_port_range(self):
        """Port range should expand correctly."""
        result = parse_ports(["8000-8003"])
        assert result == [8000, 8001, 8002, 8003]

    def test_mixed_ports_and_ranges(self):
        """Mix of single ports and ranges should parse correctly."""
        result = parse_ports(["80", "8000-8002", "443"])
        assert result == [80, 8000, 8001, 8002, 443]

    def test_invalid_port_string(self):
        """Non-numeric port should raise InvalidPortError."""
        with pytest.raises(InvalidPortError):
            parse_ports(["abc"])

    def test_invalid_range_format(self):
        """Malformed range should raise InvalidRangeError."""
        with pytest.raises(InvalidRangeError):
            parse_ports(["8000-8001-8002"])

    def test_invalid_range_non_numeric(self):
        """Non-numeric range should raise InvalidRangeError."""
        with pytest.raises(InvalidRangeError):
            parse_ports(["abc-def"])

    def test_range_start_greater_than_end(self):
        """Range with start > end should raise InvalidRangeError."""
        with pytest.raises(InvalidRangeError):
            parse_ports(["8010-8000"])

    def test_range_with_spaces(self):
        """Range with spaces should parse correctly."""
        result = parse_ports([" 8000 - 8002 "])
        assert result == [8000, 8001, 8002]

    def test_port_out_of_range(self):
        """Port outside valid range should raise InvalidPortError."""
        with pytest.raises(InvalidPortError):
            parse_ports(["70000"])

    def test_empty_ports_list(self):
        """Empty ports list should return empty result."""
        assert parse_ports([]) == []


class TestResolveHostAddresses:
    """Test hostname address resolution."""

    def test_resolve_localhost_ipv4(self):
        """localhost should resolve to at least IPv4."""
        addresses = _resolve_host_addresses("localhost")
        assert len(addresses) > 0
        # Should have at least one result
        assert any(addr[1] == "127.0.0.1" for addr in addresses)

    def test_resolve_localhost_ipv6(self):
        """localhost may resolve to IPv6 if available."""
        try:
            addresses = _resolve_host_addresses("localhost")
            # IPv6 loopback should be in the results on systems with IPv6
            # May or may not have IPv6, but if present, should be valid
            assert len(addresses) > 0
        except InvalidHostError:
            pytest.skip("IPv6 not available")

    def test_resolve_invalid_host(self):
        """Invalid hostname should raise InvalidHostError."""
        with pytest.raises(InvalidHostError):
            _resolve_host_addresses("invalid.hostname.that.does.not.exist.local")

    def test_resolve_ipv4_address(self):
        """IPv4 address should resolve to itself."""
        addresses = _resolve_host_addresses("127.0.0.1")
        assert len(addresses) > 0
        # First result should include the IP
        assert any(addr[1] == "127.0.0.1" for addr in addresses)

    def test_resolve_ipv6_address(self):
        """IPv6 address should resolve to itself if supported."""
        try:
            addresses = _resolve_host_addresses("::1")
            assert len(addresses) > 0
            # Should have the IPv6 loopback
            assert any(addr[1] == "::1" for addr in addresses)
        except InvalidHostError:
            pytest.skip("IPv6 not available on this system")


class TestCheckPort:
    """Test single port checking."""

    def test_open_port(self):
        """Test detecting an open port."""
        # Create a simple server socket to have an open port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(("127.0.0.1", 0))
            server.listen(1)
            _, port = server.getsockname()

            result = check_port("127.0.0.1", port, timeout=2.0)

            assert result.port == port
            assert result.status == "open"
            assert result.error is None

    def test_closed_port(self):
        """Test detecting a closed port."""
        # Get an ephemeral port, close the listener, then check it
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("127.0.0.1", 0))
            _, closed_port = sock.getsockname()
        # Socket closed, port should be available but not listening
        result = check_port("127.0.0.1", closed_port, timeout=0.5)

        assert result.port == closed_port
        assert result.status == "closed"

    def test_invalid_port_number(self):
        """Invalid port should raise InvalidPortError."""
        with pytest.raises(InvalidPortError):
            check_port("localhost", 70000)

    def test_invalid_host(self):
        """Invalid hostname should return closed port with error."""
        result = check_port("invalid.hostname.definitely.does.not.exist.local", 80)

        assert result.status == "closed"
        assert result.error is not None

    def test_timeout_parameter(self):
        """Check that timeout parameter is used."""
        # Get an ephemeral port, close the listener, then check it
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("127.0.0.1", 0))
            _, closed_port = sock.getsockname()
        # Socket closed, port should be available but not listening
        result = check_port("127.0.0.1", closed_port, timeout=0.1)
        assert result.status == "closed"

    def test_ipv4_localhost(self):
        """Test checking IPv4 localhost port."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(("127.0.0.1", 0))
            server.listen(1)
            _, port = server.getsockname()

            result = check_port("127.0.0.1", port, timeout=2.0)
            assert result.port == port
            assert result.status == "open"

    def test_ipv6_localhost(self):
        """Test checking IPv6 localhost port if available."""
        try:
            with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as server:
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server.bind(("::1", 0))
                server.listen(1)
                # IPv6 getsockname returns (host, port, flowinfo, scope_id)
                sockinfo = server.getsockname()
                port = sockinfo[1]

                result = check_port("::1", port, timeout=2.0)
                assert result.port == port
                assert result.status == "open"
        except OSError:
            pytest.skip("IPv6 not available on this system")

    def test_multiple_resolved_addresses_fallback(self):
        """Test that checker tries all resolved addresses."""
        # localhost typically resolves to both IPv4 and IPv6
        # This tests that if one address fails, others are tried
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(("127.0.0.1", 0))
            server.listen(1)
            _, port = server.getsockname()

            # Check via localhost, which may resolve to multiple addresses
            result = check_port("localhost", port, timeout=2.0)
            # Should succeed if any address works
            assert result.status == "open"


class TestCheckPorts:
    """Test checking multiple ports."""

    def test_check_multiple_ports(self):
        """Test checking multiple ports returns multiple results."""
        # Create a listening socket and get two closed ports
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(("127.0.0.1", 0))
            server.listen(1)
            _, open_port = server.getsockname()

            # Get two closed ports
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock1:
                sock1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock1.bind(("127.0.0.1", 0))
                _, closed_port1 = sock1.getsockname()

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock2:
                sock2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock2.bind(("127.0.0.1", 0))
                _, closed_port2 = sock2.getsockname()

            ports = [open_port, closed_port1, closed_port2]
            result = check_ports("127.0.0.1", ports, timeout=0.5)

            assert result.host == "127.0.0.1"
            assert len(result.results) == 3
            assert result.results[0].status == "open"
            assert result.results[1].status == "closed"
            assert result.results[2].status == "closed"

    def test_all_open_property(self):
        """all_open should return True only if all ports are open."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(("127.0.0.1", 0))
            server.listen(1)
            _, open_port = server.getsockname()

            result1 = check_ports("127.0.0.1", [open_port], timeout=0.5)
            assert result1.all_open is True

            # Get a closed port
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind(("127.0.0.1", 0))
                _, closed_port = sock.getsockname()

            result2 = check_ports("127.0.0.1", [open_port, closed_port], timeout=0.5)
            assert result2.all_open is False

    def test_any_open_property(self):
        """any_open should return True if at least one port is open."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(("127.0.0.1", 0))
            server.listen(1)
            _, open_port = server.getsockname()

            # Get two closed ports
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock1:
                sock1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock1.bind(("127.0.0.1", 0))
                _, closed_port1 = sock1.getsockname()

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock2:
                sock2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock2.bind(("127.0.0.1", 0))
                _, closed_port2 = sock2.getsockname()

            result1 = check_ports("127.0.0.1", [closed_port1, closed_port2], timeout=0.5)
            assert result1.any_open is False

            result2 = check_ports("127.0.0.1", [open_port, closed_port1], timeout=0.5)
            assert result2.any_open is True


class TestResultModels:
    """Test result data models."""

    def test_port_result_to_dict(self):
        """PortResult should convert to dict correctly."""
        result = PortResult(port=80, status="open")
        d = result.to_dict()

        assert d["port"] == 80
        assert d["status"] == "open"
        assert "error" not in d

    def test_port_result_with_error_to_dict(self):
        """PortResult with error should include error in dict."""
        result = PortResult(port=80, status="closed", error="Connection refused")
        d = result.to_dict()

        assert d["port"] == 80
        assert d["status"] == "closed"
        assert d["error"] == "Connection refused"

    def test_check_result_to_dict(self):
        """CheckResult should convert to dict correctly."""
        results = [
            PortResult(port=80, status="open"),
            PortResult(port=443, status="closed"),
        ]
        check_result = CheckResult(host="localhost", results=results, timeout=2.0)
        d = check_result.to_dict()

        assert d["host"] == "localhost"
        assert len(d["results"]) == 2
        assert d["results"][0]["port"] == 80
        assert d["results"][0]["status"] == "open"
        assert d["results"][1]["port"] == 443
        assert d["results"][1]["status"] == "closed"
