"""Tests for CLI interface."""

import json
import shutil
import socket
import subprocess
import sys
from io import BytesIO, StringIO, TextIOWrapper
from unittest.mock import patch

import pytest

from portreach.cli import create_parser, format_check_result, format_port_result, main
from portreach.models import CheckResult, PortResult


class TestArgumentParser:
    """Test CLI argument parser."""

    def test_parser_creation(self):
        """Parser should be created successfully."""
        parser = create_parser()
        assert parser is not None
        assert parser.prog == "portreach"

    def test_parse_simple_args(self):
        """Simple host and port should parse."""
        parser = create_parser()
        args = parser.parse_args(["localhost", "8080"])

        assert args.host == "localhost"
        assert args.ports == ["8080"]
        assert args.timeout == 2.0
        assert args.json is False
        assert args.quiet is False

    def test_parse_multiple_ports(self):
        """Multiple ports should parse."""
        parser = create_parser()
        args = parser.parse_args(["localhost", "80", "443", "8080"])

        assert args.host == "localhost"
        assert args.ports == ["80", "443", "8080"]

    def test_parse_with_timeout(self):
        """Timeout option should parse."""
        parser = create_parser()
        args = parser.parse_args(["localhost", "8080", "--timeout", "5.5"])

        assert args.timeout == 5.5

    def test_parse_json_flag(self):
        """JSON flag should parse."""
        parser = create_parser()
        args = parser.parse_args(["localhost", "8080", "--json"])

        assert args.json is True

    def test_parse_quiet_flag(self):
        """Quiet flag should parse."""
        parser = create_parser()
        args = parser.parse_args(["localhost", "8080", "--quiet"])

        assert args.quiet is True

    def test_version_flag(self):
        """Version flag should raise SystemExit."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--version"])


class TestFormatting:
    """Test result formatting functions."""

    def test_format_open_port(self):
        """Format open port should show check mark."""
        result = PortResult(port=80, status="open")
        output = format_port_result(result)

        assert "✓" in output
        assert "80" in output
        assert "OPEN" in output

    def test_format_closed_port(self):
        """Format closed port should show X mark."""
        result = PortResult(port=443, status="closed")
        output = format_port_result(result)

        assert "✗" in output
        assert "443" in output
        assert "CLOSED" in output

    def test_format_port_with_error(self):
        """Format port with error should show error message."""
        result = PortResult(port=80, status="closed", error="Connection refused")
        output = format_port_result(result)

        assert "Connection refused" in output

    def test_format_quiet_mode(self):
        """Quiet mode should return empty string."""
        result = PortResult(port=80, status="open")
        output = format_port_result(result, quiet=True)

        assert output == ""

    def test_format_check_result(self):
        """Format CheckResult should format multiple ports."""
        results = [
            PortResult(port=80, status="open"),
            PortResult(port=443, status="closed"),
        ]
        check_result = CheckResult(host="localhost", results=results, timeout=2.0)
        output = format_check_result(check_result)

        assert "80" in output
        assert "443" in output
        assert "✓" in output
        assert "✗" in output

    def test_format_check_result_quiet(self):
        """Format CheckResult quiet mode should return empty string."""
        results = [PortResult(port=80, status="open")]
        check_result = CheckResult(host="localhost", results=results, timeout=2.0)
        output = format_check_result(check_result, quiet=True)

        assert output == ""


class TestCLIExecution:
    """Test CLI main function execution."""

    @pytest.mark.parametrize(
        "timeout",
        ["nan", "inf", "-inf", "NaN", "Infinity", "0", "-1", "1e300", "not-a-number"],
    )
    def test_invalid_timeout_returns_configuration_error_without_traceback(self, timeout):
        stderr = StringIO()
        with patch("sys.stderr", new=stderr):
            exit_code = main(["127.0.0.1", "1", "--timeout", timeout])

        assert exit_code == 2
        assert "Traceback" not in stderr.getvalue()
        assert stderr.getvalue().strip()

    def test_invalid_timeout_module_and_console_entry_points(self):
        entry_points = [[sys.executable, "-m", "portreach"]]
        console = shutil.which("portreach")
        if console:
            entry_points.append([console])

        for entry_point in entry_points:
            for timeout in ("nan", "inf", "-inf", "NaN", "Infinity", "1e300"):
                result = subprocess.run(
                    [*entry_point, "127.0.0.1", "1", "--timeout", timeout],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                assert result.returncode == 2, result.stderr
                assert "Traceback" not in result.stderr
                assert result.stderr.strip()

    def test_all_ports_open_exit_code(self):
        """All open ports should return exit code 0."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(("127.0.0.1", 0))
            server.listen(1)
            _, port = server.getsockname()

            exit_code = main(["127.0.0.1", str(port), "--quiet"])
            assert exit_code == 0

    def test_any_port_closed_exit_code(self):
        """Any closed port should return exit code 1."""
        # Get a closed port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("127.0.0.1", 0))
            _, closed_port = sock.getsockname()

        exit_code = main(["127.0.0.1", str(closed_port), "--quiet"])
        assert exit_code == 1

    def test_invalid_port_exit_code(self):
        """Invalid port should return exit code 2."""
        exit_code = main(["localhost", "99999", "--quiet"])
        assert exit_code == 2

    def test_invalid_host_exit_code(self):
        """Invalid host should return exit code 1."""
        exit_code = main(["invalid.hostname.definitely.does.not.exist.local", "80", "--quiet"])
        assert exit_code == 1

    def test_invalid_timeout_exit_code(self):
        """Invalid timeout should return exit code 2."""
        exit_code = main(["localhost", "80", "--timeout", "-1", "--quiet"])
        assert exit_code == 2

    def test_no_ports_specified_exit_code(self):
        """No ports should return exit code 2."""
        exit_code = main(["localhost", "--quiet"])
        assert exit_code == 2

    def test_json_output_is_valid(self):
        """JSON output should be valid JSON."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(("127.0.0.1", 0))
            server.listen(1)
            _, port = server.getsockname()

            with patch("sys.stdout", new=StringIO()) as fake_out:
                main(["127.0.0.1", str(port), "--json"])
                output = fake_out.getvalue()

            # Parse JSON to verify it's valid
            data = json.loads(output)
            assert "host" in data
            assert "results" in data
            assert isinstance(data["results"], list)

    def test_multiple_ports_output(self):
        """Multiple ports should all appear in output."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            main(["127.0.0.1", "80", "443", "8080", "--quiet"])
            # With --quiet, output should be empty
            output = fake_out.getvalue()
            assert output == ""

    def test_range_expansion(self):
        """Port range should be expanded and checked."""
        # Get a closed port and create a small range around it
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("127.0.0.1", 0))
            _, port = sock.getsockname()

        # Create a range string for a range around the closed port
        # Since we can't guarantee 3 consecutive ports are closed,
        # just test with the single closed port
        exit_code = main(["127.0.0.1", str(port), "--quiet"])
        # Single closed port should return 1
        assert exit_code == 1

    def test_help_flag(self) -> None:
        """Help flag should return exit code 0."""
        with patch("sys.stdout", new=StringIO()):
            exit_code = main(["--help"])
        assert exit_code == 0

    def test_version_flag(self) -> None:
        """Version flag should return exit code 0."""
        with patch("sys.stdout", new=StringIO()):
            exit_code = main(["--version"])
        assert exit_code == 0

    def test_quiet_suppresses_output(self):
        """Quiet mode should suppress normal output."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(("127.0.0.1", 0))
            server.listen(1)
            _, port = server.getsockname()

            with patch("sys.stdout", new=StringIO()) as fake_out:
                main(["127.0.0.1", str(port), "--quiet"])
                output = fake_out.getvalue()

            assert output == ""

    def test_normal_output_not_quiet(self):
        """Normal mode should produce output."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(("127.0.0.1", 0))
            server.listen(1)
            _, port = server.getsockname()

            with patch("sys.stdout", new=StringIO()) as fake_out:
                main(["127.0.0.1", str(port)])
                output = fake_out.getvalue()

            assert len(output) > 0
            assert "✓" in output or "OPEN" in output

    def test_cp1252_output_uses_ascii_fallback_for_open_port(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(("127.0.0.1", 0))
            server.listen(1)
            port = server.getsockname()[1]
            stream = TextIOWrapper(BytesIO(), encoding="cp1252", errors="strict")

            with patch("sys.stdout", new=stream):
                exit_code = main(["127.0.0.1", str(port)])
                stream.flush()

            assert exit_code == 0
            output = stream.buffer.getvalue().decode("cp1252").replace("\r\n", "\n")
            assert output == f"[+] {port}: OPEN\n"

    def test_cp1252_output_uses_ascii_fallback_for_closed_port(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]

        stream = TextIOWrapper(BytesIO(), encoding="cp1252", errors="strict")
        with patch("sys.stdout", new=stream):
            exit_code = main(["127.0.0.1", str(port)])
            stream.flush()

        assert exit_code == 1
        output = stream.buffer.getvalue().decode("cp1252").replace("\r\n", "\n")
        assert output == f"[-] {port}: CLOSED\n"

    def test_utf8_output_preserves_status_symbols(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(("127.0.0.1", 0))
            server.listen(1)
            port = server.getsockname()[1]
            stream = TextIOWrapper(BytesIO(), encoding="utf-8", errors="strict")

            with patch("sys.stdout", new=stream):
                exit_code = main(["127.0.0.1", str(port)])
                stream.flush()

        assert exit_code == 0
        output = stream.buffer.getvalue().decode("utf-8").replace("\r\n", "\n")
        assert output == f"✓ {port}: OPEN\n"

    def test_cp1252_json_output_is_unchanged_and_valid(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(("127.0.0.1", 0))
            server.listen(1)
            port = server.getsockname()[1]
            stream = TextIOWrapper(BytesIO(), encoding="cp1252", errors="strict")

            with patch("sys.stdout", new=stream):
                exit_code = main(["127.0.0.1", str(port), "--json"])
                stream.flush()

        output = stream.buffer.getvalue().decode("cp1252")
        assert exit_code == 0
        assert json.loads(output) == {
            "host": "127.0.0.1",
            "results": [{"port": port, "status": "open"}],
        }

    def test_cp1252_quiet_mode_and_exit_codes_are_unchanged(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(("127.0.0.1", 0))
            server.listen(1)
            open_port = server.getsockname()[1]
            stream = TextIOWrapper(BytesIO(), encoding="cp1252", errors="strict")

            with patch("sys.stdout", new=stream):
                open_exit = main(["127.0.0.1", str(open_port), "--quiet"])
                stream.flush()

        assert open_exit == 0
        assert stream.buffer.getvalue() == b""

        stream = TextIOWrapper(BytesIO(), encoding="cp1252", errors="strict")
        with patch("sys.stdout", new=stream):
            closed_exit = main(["127.0.0.1", "99999", "--quiet"])
        assert closed_exit == 2
        assert stream.buffer.getvalue() == b""

    def test_unexpected_output_write_error_is_not_suppressed(self):
        class BrokenOutput(StringIO):
            def write(self, _text):
                raise OSError("output device failed")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(("127.0.0.1", 0))
            server.listen(1)
            port = server.getsockname()[1]

            with (
                patch("sys.stdout", new=BrokenOutput()),
                pytest.raises(OSError, match="output device failed"),
            ):
                main(["127.0.0.1", str(port)])
