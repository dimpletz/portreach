"""Command-line interface for PortReach."""

import argparse
import json
import sys
from typing import TextIO

from portreach import __version__
from portreach.checker import check_ports, parse_ports
from portreach.exceptions import PortReachError
from portreach.models import CheckResult, PortResult


def format_port_result(result: PortResult, quiet: bool = False) -> str:
    """Format a single port result for display.

    Args:
        result: PortResult object.
        quiet: If True, return empty string.

    Returns:
        Formatted result string.
    """
    if quiet:
        return ""

    status_symbol = "✓" if result.status == "open" else "✗"
    status_text = result.status.upper()

    if result.error:
        return f"{status_symbol} {result.port}: {result.error}"
    return f"{status_symbol} {result.port}: {status_text}"


def format_check_result(check_result: CheckResult, quiet: bool = False) -> str:
    """Format a CheckResult for CLI display.

    Args:
        check_result: CheckResult object.
        quiet: If True, return empty string.

    Returns:
        Formatted result string.
    """
    if quiet:
        return ""

    lines = []
    for result in check_result.results:
        lines.append(format_port_result(result, quiet=False))

    return "\n".join(lines)


def _write_result_output(output: str, stream: TextIO) -> None:
    encoding = getattr(stream, "encoding", None)
    if encoding is not None:
        try:
            "✓✗".encode(encoding)
        except UnicodeEncodeError:
            output = output.replace("✓", "[+]").replace("✗", "[-]")

    print(output, file=stream)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser.

    Returns:
        Configured ArgumentParser.
    """
    parser = argparse.ArgumentParser(
        prog="portreach",
        description="Check if TCP ports are open on a host.",
        epilog=(
            "Examples:\n"
            "  portreach localhost 8080\n"
            "  portreach example.com 80 443 8080\n"
            "  portreach 192.168.1.1 8000-8010\n"
            "  portreach localhost 443 --timeout 3\n"
            "  portreach localhost 80 443 --json\n"
            "  portreach localhost 443 --quiet"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    parser.add_argument(
        "host",
        help="Host to check (hostname, IPv4, or IPv6 address)",
    )

    parser.add_argument(
        "ports",
        nargs="+",
        help="Port numbers or ranges (e.g., 80 443 8000-8010)",
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=2.0,
        help="Connection timeout in seconds (default: 2.0)",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output (useful for scripts)",
    )

    return parser


def main(argv: list[str] | None = None) -> int:  # noqa: C901
    """Main entry point for the CLI.

    Args:
        argv: Command-line arguments (uses sys.argv if not provided).

    Returns:
        Exit code: 0 if all ports open, 1 if any closed, 2 on error.
    """
    parser = create_parser()

    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        # argparse calls sys.exit on error or --help
        return e.code if isinstance(e.code, int) else 2

    # Validate timeout
    if args.timeout <= 0:
        if not args.quiet:
            print("Error: timeout must be greater than 0", file=sys.stderr)
        return 2

    # Parse ports
    try:
        ports = parse_ports(args.ports)
    except PortReachError as e:
        if not args.quiet:
            print(f"Error: {e}", file=sys.stderr)
        return 2

    if not ports:
        if not args.quiet:
            print("Error: no valid ports specified", file=sys.stderr)
        return 2

    # Remove duplicates and sort for consistent output
    ports = sorted(set(ports))

    # Check ports
    try:
        result = check_ports(args.host, ports, timeout=args.timeout)
    except PortReachError as e:
        if not args.quiet:
            print(f"Error: {e}", file=sys.stderr)
        return 2

    # Output results
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        output = format_check_result(result, quiet=args.quiet)
        if output:
            _write_result_output(output, sys.stdout)

    # Return exit code based on results
    if result.all_open:
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
