#!/usr/bin/env python3
"""
Quick sanity check for PortReach v0.1.0

This script runs a quick set of basic tests to verify PortReach is working.

Run: python test_sanity_check.py
"""

import socket
import subprocess
import sys
from contextlib import contextmanager
from typing import Tuple


@contextmanager
def ephemeral_server(host: str = "127.0.0.1") -> Tuple[str, int]:
    """Create a temporary listening socket."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, 0))
        sock.listen(1)
        _, port = sock.getsockname()
        yield host, port
    finally:
        sock.close()


def run_portreach(args: list) -> Tuple[int, str]:
    """Run portreach and return (exit_code, output)."""
    result = subprocess.run(
        [sys.executable, "-m", "portreach"] + args, capture_output=True, text=True
    )
    return result.returncode, result.stdout


def main():
    """Run quick sanity checks."""
    print("\nPortReach v0.1.0 - Sanity Check\n")

    tests_passed = 0
    tests_total = 0

    # Test 1: Version
    tests_total += 1
    exit_code, output = run_portreach(["--version"])
    if exit_code == 0 and "0.1.0" in output:
        print("[OK] Version check passed")
        tests_passed += 1
    else:
        print("[FAIL] Version check failed")

    # Test 2: Help
    tests_total += 1
    exit_code, output = run_portreach(["--help"])
    if exit_code == 0 and len(output) > 100:
        print("[OK] Help check passed")
        tests_passed += 1
    else:
        print("[FAIL] Help check failed")

    # Test 3: Open port
    tests_total += 1
    with ephemeral_server() as (host, port):
        exit_code, output = run_portreach([host, str(port)])
        if exit_code == 0 and "OPEN" in output:
            print(f"[OK] Open port detection passed (port {port})")
            tests_passed += 1
        else:
            print(f"[FAIL] Open port detection failed")

    # Test 4: Closed port
    tests_total += 1
    with ephemeral_server() as (host, port):
        pass
    exit_code, output = run_portreach([host, str(port)])
    if exit_code == 1 and "CLOSED" in output:
        print(f"[OK] Closed port detection passed")
        tests_passed += 1
    else:
        print(f"[FAIL] Closed port detection failed")

    # Test 5: Invalid port (exit code 2)
    tests_total += 1
    exit_code, output = run_portreach(["localhost", "99999"])
    if exit_code == 2:
        print("[OK] Invalid port detection passed")
        tests_passed += 1
    else:
        print("[FAIL] Invalid port detection failed")

    # Test 6: JSON output
    tests_total += 1
    with ephemeral_server() as (host, port):
        exit_code, output = run_portreach([host, str(port), "--json"])
        if exit_code == 0 and '"status"' in output and '"port"' in output:
            print("[OK] JSON output passed")
            tests_passed += 1
        else:
            print("[FAIL] JSON output failed")

    # Test 7: Quiet mode
    tests_total += 1
    with ephemeral_server() as (host, port):
        exit_code, output = run_portreach([host, str(port), "--quiet"])
        if exit_code == 0 and output.strip() == "":
            print("[OK] Quiet mode passed")
            tests_passed += 1
        else:
            print("[FAIL] Quiet mode failed")

    print(f"\nResults: {tests_passed}/{tests_total} tests passed\n")
    return 0 if tests_passed == tests_total else 1


if __name__ == "__main__":
    sys.exit(main())
