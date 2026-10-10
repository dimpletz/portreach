#!/usr/bin/env python3
"""
Manual scenario testing for PortReach v0.1.0

This script tests real-world scenarios including:
- Basic port checking functionality
- Exit codes
- JSON output
- Multiple ports and ranges
- Error handling

Run: python test_manual_scenarios.py
"""

import json
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from typing import Tuple


@contextmanager
def ephemeral_server(host: str = "127.0.0.1") -> Tuple[str, int]:
    """Context manager that creates a temporary listening socket and returns (host, port)."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, 0))
        sock.listen(1)
        _, port = sock.getsockname()
        yield host, port
    finally:
        sock.close()


def run_portreach(args: list) -> Tuple[int, str, str]:
    """Run portreach command and return (exit_code, stdout, stderr)."""
    cmd = [sys.executable, "-m", "portreach"] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def test_open_port():
    """Test detection of open port."""
    print("\n[TEST 1] Open Port Detection")
    print("-" * 50)

    with ephemeral_server() as (host, port):
        print(f"Created listening socket on {host}:{port}")

        exit_code, stdout, stderr = run_portreach([host, str(port)])

        print(f"Command: portreach {host} {port}")
        print(f"Exit code: {exit_code}")
        print(f"Output:\n{stdout}")

        assert exit_code == 0, f"Expected exit code 0, got {exit_code}"
        assert "OPEN" in stdout or "open" in stdout, f"Expected 'OPEN' in output"
        print("[PASSED]")


def test_closed_port():
    """Test detection of closed port."""
    print("\n[TEST 2] Closed Port Detection")
    print("-" * 50)

    # Use port that's very unlikely to be open
    with ephemeral_server() as (host, port):
        # Close the socket immediately to ensure port is closed
        pass

    # Now port is closed
    exit_code, stdout, stderr = run_portreach([host, str(port)])

    print(f"Command: portreach {host} {port}")
    print(f"Exit code: {exit_code}")
    print(f"Output:\n{stdout}")

    assert exit_code == 1, f"Expected exit code 1, got {exit_code}"
    assert "CLOSED" in stdout or "closed" in stdout, f"Expected 'CLOSED' in output"
    print("[PASSED]")


def test_multiple_ports():
    """Test checking multiple ports."""
    print("\n[TEST 3] Multiple Ports")
    print("-" * 50)

    with ephemeral_server() as (host, open_port):
        # Create a closed port
        with ephemeral_server(host) as (_, closed_port):
            pass

        print(f"Open port: {open_port}, Closed port: {closed_port}")

        exit_code, stdout, stderr = run_portreach(
            [host, str(open_port), str(closed_port)]
        )

        print(f"Command: portreach {host} {open_port} {closed_port}")
        print(f"Exit code: {exit_code}")
        print(f"Output:\n{stdout}")

        assert exit_code == 1, f"Expected exit code 1 (mixed results), got {exit_code}"
        assert "OPEN" in stdout or "open" in stdout
        assert "CLOSED" in stdout or "closed" in stdout
    print("[PASSED]")
    """Test port range expansion."""
    print("\n[TEST 4] Port Range Expansion")
    print("-" * 50)

    with ephemeral_server() as (host, port):
        # Create range including open port
        start = port - 2 if port >= 3 else 1
        end = port + 2
        range_spec = f"{start}-{end}"

        print(f"Open port: {port}, Testing range: {range_spec}")

        exit_code, stdout, stderr = run_portreach([host, range_spec])

        print(f"Command: portreach {host} {range_spec}")
        print(f"Exit code: {exit_code}")
        print(f"Output:\n{stdout}")

        assert exit_code == 1, f"Expected exit code 1 (mixed results), got {exit_code}"
        assert str(port) in stdout, f"Expected to see port {port} in output"
    print("[PASSED]")


def test_json_output():
    """Test JSON output format."""
    print("\n[TEST 5] JSON Output")
    print("-" * 50)

    with ephemeral_server() as (host, port):
        exit_code, stdout, stderr = run_portreach([host, str(port), "--json"])

        print(f"Command: portreach {host} {port} --json")
        print(f"Exit code: {exit_code}")
        print(f"Output:\n{stdout}")

        # Parse JSON
        try:
            data = json.loads(stdout)
            assert data["host"] == host
            assert len(data["results"]) == 1
            assert data["results"][0]["port"] == port
            assert data["results"][0]["status"] == "open"
            print("[PASSED] Valid JSON format")
        except json.JSONDecodeError as e:
            raise AssertionError(f"Invalid JSON output: {e}")


def test_quiet_mode():
    """Test quiet mode suppresses output."""
    print("\n[TEST 6] Quiet Mode")
    print("-" * 50)

    with ephemeral_server() as (host, port):
        exit_code, stdout, stderr = run_portreach([host, str(port), "--quiet"])

        print(f"Command: portreach {host} {port} --quiet")
        print(f"Exit code: {exit_code}")
        print(f"Output: '{stdout}' (empty expected)")

        assert exit_code == 0, f"Expected exit code 0, got {exit_code}"
        assert stdout.strip() == "", f"Expected no output in quiet mode, got: {stdout}"
    print("[PASSED]")


def test_exit_code_all_open():
    """Test exit code 0 when all ports open."""
    print("\n[TEST 7] Exit Code 0 (All Open)")
    print("-" * 50)

    with ephemeral_server() as (host, port1):
        with ephemeral_server(host) as (_, port2):
            exit_code, stdout, stderr = run_portreach(
                [host, str(port1), str(port2), "--quiet"]
            )

            print(f"Command: portreach {host} {port1} {port2} --quiet")
            print(f"Exit code: {exit_code}")

            assert exit_code == 0, f"Expected exit code 0 (all open), got {exit_code}"
            print("[PASS]")


def test_exit_code_any_closed():
    """Test exit code 1 when any port closed."""
    print("\n[TEST 8] Exit Code 1 (Any Closed)")
    print("-" * 50)

    with ephemeral_server() as (host, open_port):
        with ephemeral_server(host) as (_, closed_port):
            pass

        exit_code, stdout, stderr = run_portreach(
            [host, str(open_port), str(closed_port), "--quiet"]
        )

        print(f"Command: portreach {host} {open_port} {closed_port} --quiet")
        print(f"Exit code: {exit_code}")

        assert exit_code == 1, f"Expected exit code 1 (any closed), got {exit_code}"
    print("[PASS]")


def test_exit_code_error():
    """Test exit code 2 for configuration errors."""
    print("\n[TEST 9] Exit Code 2 (Config Error)")
    print("-" * 50)

    # Invalid port number
    exit_code, stdout, stderr = run_portreach(["localhost", "99999"])

    print(f"Command: portreach localhost 99999")
    print(f"Exit code: {exit_code}")
    print(f"Error output:\n{stdout or stderr}")

    assert exit_code == 2, f"Expected exit code 2 (config error), got {exit_code}"
    print("[PASS]")


def test_help():
    """Test --help flag."""
    print("\n[TEST 10] Help Flag")
    print("-" * 50)

    exit_code, stdout, stderr = run_portreach(["--help"])

    print(f"Command: portreach --help")
    print(f"Exit code: {exit_code}")
    print(f"Output length: {len(stdout)} chars")

    assert exit_code == 0, f"Expected exit code 0, got {exit_code}"
    assert "usage" in stdout.lower() or "portreach" in stdout.lower()
    print("[PASS]")


def test_version():
    """Test --version flag."""
    print("\n[TEST 11] Version Flag")
    print("-" * 50)

    exit_code, stdout, stderr = run_portreach(["--version"])

    print(f"Command: portreach --version")
    print(f"Exit code: {exit_code}")
    print(f"Output: {stdout.strip()}")

    assert exit_code == 0, f"Expected exit code 0, got {exit_code}"
    assert "0.1.0" in stdout
    print("[PASS]")


def test_timeout():
    """Test timeout parameter."""
    print("\n[TEST 12] Timeout Parameter")
    print("-" * 50)

    # Use a host that's unlikely to respond quickly
    start = time.time()
    exit_code, stdout, stderr = run_portreach(["192.0.2.1", "80", "--timeout", "1"])
    elapsed = time.time() - start

    print(f"Command: portreach 192.0.2.1 80 --timeout 1")
    print(f"Exit code: {exit_code}")
    print(f"Elapsed time: {elapsed:.2f}s (expected ~1s)")

    # Should timeout around 1 second (allow some variance)
    assert 0.8 <= elapsed <= 3.0, f"Timeout not working correctly: {elapsed}s"
    print("[PASS]")


def main():
    """Run all tests."""
    print("=" * 60)
    print("PortReach v0.1.0 - Manual Scenario Tests")
    print("=" * 60)

    tests = [
        test_open_port,
        test_closed_port,
        test_multiple_ports,
        test_json_output,
        test_quiet_mode,
        test_exit_code_all_open,
        test_exit_code_any_closed,
        test_exit_code_error,
        test_help,
        test_version,
        test_timeout,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"[FAILED] {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
