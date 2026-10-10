# PortReach

A lightweight Python utility for checking TCP port connectivity. PortReach is designed for developers, DevOps engineers, and system administrators who need a fast way to diagnose network accessibility from the command line.

Release history: [CHANGELOG.md](CHANGELOG.md).

**PortReach** combines:
- **Simplicity**: Just `portreach localhost 8080` to check a port
- **Reliability**: Socket-based TCP checks with configurable timeouts
- **Speed**: Minimal startup time and low overhead
- **Cross-platform**: Works on Windows, macOS, and Linux
- **Scriptable**: Machine-readable output and predictable exit codes
- **Extensible**: Clean core API for use from Python applications

---

## Table of Contents

1. [What PortReach Does](#what-portreach-does)
2. [Why PortReach Is Useful](#why-portreach-is-useful)
3. [Key Features](#key-features)
4. [Requirements](#requirements)
5. [Installation](#installation)
   - [From PyPI](#from-pypi)
   - [From Source](#from-source)
6. [Quick Start](#quick-start)
7. [Usage Guide](#usage-guide)
   - [CLI Syntax](#cli-syntax)
   - [Single Port](#single-port)
   - [Multiple Ports](#multiple-ports)
   - [Port Ranges](#port-ranges)
   - [Timeout Configuration](#timeout-configuration)
   - [JSON Output](#json-output)
   - [Quiet Mode](#quiet-mode)
   - [Exit Codes](#exit-codes)
8. [Host Support](#host-support)
   - [Hostnames](#hostnames)
   - [IPv4 Addresses](#ipv4-addresses)
   - [IPv6 Addresses](#ipv6-addresses)
9. [Python API](#python-api)
10. [Error Handling](#error-handling)
11. [Common Use Cases](#common-use-cases)
12. [Development](#development)
    - [Setup](#setup)
    - [Running Tests](#running-tests)
    - [Type Checking](#type-checking)
    - [Code Quality](#code-quality)
13. [Project Structure](#project-structure)
14. [Contributing](#contributing)
15. [Security and Scope](#security-and-scope)
16. [Roadmap](#roadmap)
17. [License](#license)
18. [Author](#author)

---

## What PortReach Does

PortReach performs **TCP connectivity checks** by attempting to establish a socket connection to a specified host and port. It reports whether each port is reachable (open) or not (closed).

Key capabilities:
- Check individual ports
- Check multiple ports in a single invocation
- Expand port ranges (e.g., `8000-8010` → check ports 8000 through 8010)
- Resolve DNS hostnames to IP addresses
- Customize connection timeouts
- Output results in human-readable or JSON format
- Generate predictable exit codes for automation

---

## Why PortReach Is Useful

### Common Scenarios

**Local Development**
```bash
# Verify your development server is running
portreach localhost 3000
# Check multiple service ports at once
portreach localhost 3000 5432 6379
```

**Deployment Verification**
```bash
# Confirm application port is accessible after deployment
portreach api.example.com 443 --timeout 5
# Check a range of worker ports on a load balancer
portreach lb.internal 8000-8010
```

**CI/CD Pipelines**
```bash
# Exit code 0 if port is open, 1 if closed
portreach app-server 5000 --quiet
if [ $? -eq 0 ]; then
  echo "Health check passed"
  exit 0
else
  echo "Service is not responding"
  exit 1
fi
```

**Container Health Checks**
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD portreach localhost 8080 --quiet
```

**Troubleshooting Connectivity**
```bash
# Is the firewall blocking port 443?
portreach example.com 443
# Which database ports are accessible from this host?
portreach db-server 3306 5432 27017
```

### Why Not Other Tools?

| Feature | PortReach | netcat | telnet | curl | nc |
|---------|-----------|--------|--------|------|-----|
| Pure Python | ✓ | ✗ | ✗ | ✗ | ✗ |
| No Dependencies | ✓ | N/A | N/A | N/A | N/A |
| Cross-Platform | ✓ | ✓ | ✗ | ✓ | ✓ |
| JSON Output | ✓ | ✗ | ✗ | ✓ | ✗ |
| Port Ranges | ✓ | ✗ | ✗ | ✗ | ✗ |
| Easy Install | ✓ | N/A | N/A | ✓ | ✗ |
| Python API | ✓ | ✗ | ✗ | ✗ | ✗ |

---

## Key Features

✅ **Lightweight and Fast**
- Pure Python implementation
- No external dependencies at runtime
- Minimal memory footprint
- Low startup overhead

✅ **Simple, Intuitive CLI**
- Clear, readable output with visual indicators (✓/✗)
- Sensible defaults (2-second timeout)
- Comprehensive help text (`portreach --help`)

✅ **Flexible Input**
- Individual ports: `80 443 8080`
- Ranges: `8000-8010`
- Mixed: `80 443 8000-8005 9000`

✅ **Multiple Output Formats**
- Human-readable (default)
- JSON for integration with other tools
- Quiet mode for scripts

✅ **Reliable Exit Codes**
- `0`: All ports open
- `1`: One or more ports closed
- `2`: Configuration error (invalid arguments, invalid ports/ranges, invalid timeout, etc.)

✅ **Robust Error Handling**
- DNS resolution failures are handled gracefully
- Connection timeouts are configurable
- Clear error messages without Python tracebacks

✅ **Typed Python API**
- Type-annotated Python functions
- Reusable in other applications
- Suitable for scripting and automation

---

## Requirements

- **Python 3.10 or later** (3.10, 3.11, 3.12, 3.13 tested)
- **Operating System**: Windows, macOS, or Linux
- **Network Access**: Ability to create TCP sockets to target hosts/ports
- **No external dependencies** at runtime

PortReach preserves the `✓` and `✗` status symbols when the output stream supports them and uses `[+]` and `[-]` when it does not.

### Python Version Support

| Version | Support |
|---------|---------|
| Python 3.10 | ✓ Supported |
| Python 3.11 | ✓ Supported |
| Python 3.12 | ✓ Supported |
| Python 3.13 | ✓ Supported |
| Python 3.9 and earlier | ✗ Not supported |

---

## Installation

### From PyPI

PortReach v0.1.0 has not been published to PyPI. Install from source using the instructions below; do not use `pip install portreach` until a release is published.

### From Source

Clone the repository and install in development mode:

```bash
git clone https://github.com/dimpletz/portreach.git
cd portreach
```

For development (including test dependencies):

```bash
pip install -e ".[dev]"
```

---

## Quick Start

The commands below show syntax only; their output depends on whether the example target and port are reachable.

### Check if a port is open

```bash
$ portreach localhost 8080
✓ 8080: OPEN
```

### Check if a port is not accessible

```bash
$ portreach localhost 9999
✗ 9999: CLOSED
```

### Check multiple ports

```bash
$ portreach example.com 80 443 8080
✓ 80: OPEN
✓ 443: OPEN
✗ 8080: CLOSED
```

### Use quiet mode for scripts

```bash
$ portreach localhost 3000 --quiet
$ echo $?
0
```

### Get JSON output

```bash
$ portreach localhost 8080 --json
{
  "host": "localhost",
  "results": [
    {
      "port": 8080,
      "status": "open"
    }
  ]
}
```

---

## Usage Guide

### CLI Syntax

```text
portreach HOST PORT [PORT ...] [OPTIONS]

Positional Arguments:
  HOST                  Hostname, IPv4 address, or IPv6 address to check
  PORT                  Port numbers or ranges (e.g., 80 443 8000-8010)

Options:
  --timeout SECONDS     Connection timeout in seconds (default: 2.0)
  --json               Output results as JSON
  --quiet              Suppress all output (useful for scripts)
  --version            Show program version
  --help               Show this help message
```

### Single Port

Check a single port on a host:

```bash
# Check localhost
$ portreach localhost 8080

# Check a domain
$ portreach example.com 443

# Check an IP address
$ portreach 192.168.1.100 22
```

Output:
```text
✓ 8080: OPEN
```
or
```text
✗ 8080: CLOSED
```

### Multiple Ports

Check several ports in one command:

```bash
$ portreach example.com 80 443 8080 9000
```

Output:
```text
✓ 80: OPEN
✓ 443: OPEN
✗ 8080: CLOSED
✗ 9000: CLOSED
```

Ports are checked sequentially. Duplicates are automatically removed and results are sorted.

### Port Ranges

Expand a range of ports:

```bash
# Check ports 8000 through 8010
$ portreach localhost 8000-8010
```

Output:
```text
✓ 8000: OPEN
✓ 8001: OPEN
✓ 8002: OPEN
✓ 8003: OPEN
✓ 8004: OPEN
✗ 8005: CLOSED
✗ 8006: CLOSED
✗ 8007: CLOSED
✗ 8008: CLOSED
✗ 8009: CLOSED
✗ 8010: CLOSED
```

Mix individual ports and ranges:

```bash
$ portreach localhost 80 443 8000-8005 9000
```

Port ranges must be valid:
- Both start and end must be integers between 1 and 65535
- Start port must be ≤ end port

### Timeout Configuration

By default, PortReach waits 2 seconds for a connection:

```bash
$ portreach example.com 443 --timeout 2
```

For slow networks or distant hosts, increase the timeout:

```bash
$ portreach slow-server.example.com 443 --timeout 10
```

For quick checks on your local network:

```bash
$ portreach 192.168.1.1 22 --timeout 1
```

**Note**: Timeout must be a positive number (in seconds).

### JSON Output

Get structured output for programmatic use:

```bash
$ portreach localhost 80 443 --json
```

Output:
```json
{
  "host": "localhost",
  "results": [
    {
      "port": 80,
      "status": "open"
    },
    {
      "port": 443,
      "status": "closed"
    }
  ]
}
```

Fields:
- `host` (string): The hostname or IP address checked
- `results` (array): Result for each port
  - `port` (int): Port number
  - `status` (string): `"open"` or `"closed"`
  - `error` (string, optional): Platform-dependent resolver diagnostic when hostname resolution fails

### Quiet Mode

Suppress normal per-port result output for valid requests; rely on exit codes. Argument-parser diagnostics can still be printed for malformed invocations:

```bash
$ portreach localhost 8080 --quiet
$ echo $?
0
```

No output is printed. Check the exit code to determine the result:
- `0` = all ports open
- `1` = any port closed
- `2` = error

Useful in shell scripts:

```bash
#!/bin/bash
portreach app-server 3000 --quiet
if [ $? -eq 0 ]; then
  echo "Application is running"
else
  echo "Application is not responding"
  exit 1
fi
```

### Exit Codes

PortReach returns specific exit codes for automation and CI/CD:

| Code | Meaning | Example |
|------|---------|---------|
| `0` | **Success**: All requested ports are open | `portreach localhost 8080` (port open) |
| `1` | **Failure**: One or more ports are closed | `portreach localhost 9999` (port closed) |
| `2` | **Error**: Invalid arguments or configuration error | `portreach localhost 70000` (invalid port) |

#### Examples

All ports open → exit 0:
```bash
$ portreach localhost 80 443 --quiet
$ echo $?
0
```

Port closed → exit 1:
```bash
$ portreach localhost 9999 --quiet
$ echo $?
1
```

Invalid port → exit 2:
```bash
$ portreach localhost 70000 --quiet
$ echo $?
2
```

---

## Host Support

### Hostnames

Resolve and check hosts by DNS name:

```bash
$ portreach example.com 80
$ portreach api.internal.company.com 443
$ portreach localhost 8080
```

DNS resolution happens automatically. If a hostname cannot be resolved, PortReach reports the port as closed with an error message.

### IPv4 Addresses

Check IPv4 addresses directly (no DNS lookup needed):

```bash
$ portreach 127.0.0.1 8080
$ portreach 192.168.1.1 22
$ portreach 10.0.0.5 443
```

### IPv6 Addresses

IPv6 is supported on systems with IPv6 network stack:

```bash
$ portreach ::1 8080
$ portreach 2001:db8::1 443
```

**Note**: IPv6 support depends on your operating system and network configuration. Use the IPv6 address in standard notation (colons and hex digits).

---

## Python API

Use PortReach programmatically in your Python applications.

### Check a Single Port

```python
from portreach import check_port

result = check_port("localhost", 8080)
print(result.status)  # "open" or "closed"
print(result.port)    # 8080
```

### Check Multiple Ports

```python
from portreach import check_ports

result = check_ports("example.com", [80, 443, 8080])

# Check if all ports are open
if result.all_open:
    print("All ports are accessible")

# Check if any port is open
if result.any_open:
    print("At least one port is accessible")

# Iterate through results
for port_result in result.results:
    print(f"Port {port_result.port}: {port_result.status}")
```

### Serialize Results to JSON

```python
from portreach import check_ports
import json

result = check_ports("localhost", [80, 443])
json_data = result.to_dict()
print(json.dumps(json_data, indent=2))
```

Output:
```json
{
  "host": "localhost",
  "results": [
    {
      "port": 80,
      "status": "open"
    },
    {
      "port": 443,
      "status": "closed"
    }
  ]
}
```

### Parse Port Specifications

```python
from portreach.checker import parse_ports

ports = parse_ports(["80", "443", "8000-8010"])
print(ports)  # [80, 443, 8000, 8001, ..., 8010]
```

### Custom Timeout

```python
from portreach import check_port

result = check_port("slow-server.example.com", 443, timeout=5.0)
```

### Exception Handling

Invalid port values raise `InvalidPortError`. Hostname resolution failures are returned as a closed result with an `error` message; they are not raised by `check_port`:

```python
from portreach import InvalidPortError, check_port

try:
    result = check_port("localhost", 0)
except InvalidPortError as e:
    print(f"Invalid port: {e}")

result = check_port("localhost", 80)
if result.error:
    print(f"Host resolution failed: {result.error}")
```

### Result Objects

PortReach uses typed models for results:

```python
from portreach import check_ports
from portreach.models import CheckResult, PortResult

result: CheckResult = check_ports("localhost", [80, 443])

# CheckResult properties
print(result.host)       # "localhost"
print(result.timeout)    # 2.0
print(result.all_open)   # bool: True if all ports open
print(result.any_open)   # bool: True if any port open

# PortResult objects
for port_result in result.results:
    print(port_result.port)     # int
    print(port_result.status)   # "open" or "closed"
    print(port_result.error)    # str or None
```

---

## Error Handling

PortReach handles errors gracefully and provides clear error messages.

### Hostname Resolution Failure

If a hostname cannot be resolved, the port is reported as closed with an error message:

```bash
$ portreach invalid.hostname.local 80
✗ 80: Could not resolve hostname 'invalid.hostname.local': <system resolver message>
```

Exit code: `1` (port unreachable)

### Invalid Port Number

Ports must be between 1 and 65535:

```bash
$ portreach localhost 99999
Error: Port must be between 1 and 65535, got 99999
```

Exit code: `2` (configuration error)

### Invalid Port Range

Port ranges must have start ≤ end:

```bash
$ portreach localhost 8010-8000
Error: Invalid port range: 8010-8000 (start 8010 > end 8000)
```

Exit code: `2`

### Malformed Arguments

```bash
$ portreach localhost abc
Error: Invalid port number: abc
```

Exit code: `2`

### Connection Timeout

If a connection takes longer than the timeout, the port is reported as closed:

```bash
$ portreach unreachable-host 80 --timeout 1
✗ 80: CLOSED
```

No error is shown (timeout is normal for closed/unreachable ports).

### No Ports Specified

If no port arguments are provided:

```bash
$ portreach localhost
Error: no valid ports specified
```

Exit code: `2`

---

## Common Use Cases

### Health Check in CI/CD Pipeline

```bash
#!/bin/bash
set -e

# Wait for application to start
sleep 5

# Check application port
if portreach localhost 8080 --quiet; then
  echo "✓ Application is running"
else
  echo "✗ Application failed to start"
  exit 1
fi
```

### Docker Health Check

```dockerfile
FROM python:3.12-slim

COPY . .
RUN pip install .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD portreach localhost 8000 --quiet

CMD ["python", "-m", "myapp"]
```

### Post-Deployment Verification

```bash
#!/bin/bash

ENVIRONMENT=$1
SERVERS=("api1.example.com" "api2.example.com" "api3.example.com")
PORTS=(80 443 8080)

echo "Verifying deployment to $ENVIRONMENT..."

for server in "${SERVERS[@]}"; do
  echo "Checking $server..."
  for port in "${PORTS[@]}"; do
    if ! portreach "$server" "$port" --timeout 5 --quiet; then
      echo "✗ Failed: $server:$port"
      exit 1
    fi
  done
  echo "✓ $server is healthy"
done

echo "✓ All servers healthy"
```

### Firewall Rule Validation

```bash
#!/bin/bash

# Test if firewall allows access to required ports
echo "Testing firewall rules..."

if portreach api.internal 443 --quiet && \
   portreach db.internal 5432 --quiet && \
   portreach cache.internal 6379 --quiet; then
  echo "✓ All firewall rules verified"
else
  echo "✗ Firewall rule violation detected"
  exit 1
fi
```

### Network Diagnostics

```bash
# Check which ports are open on a server
portreach myserver 22 80 443 3306 5432 6379 8080

# Check a range of ports (e.g., application worker ports)
portreach load-balancer 8000-8010

# Verify DNS and connectivity
portreach example.com 443 --timeout 5

# Check multiple internal services
portreach 192.168.1.10 3000 5000 8000
```

---

## Development

### Setup

Clone the repository and install:

```bash
git clone https://github.com/dimpletz/portreach.git
cd portreach
pip install -e ".[dev]"
```

This installs:
- `pytest` for testing
- `pytest-cov` for coverage
- `mypy` for type checking
- `ruff` for linting and formatting

### Running Tests

Run the full test suite:

```bash
pytest
```

Run with verbose output:

```bash
pytest -v
```

Run with coverage report:

```bash
pytest --cov=src/portreach --cov-report=html
```

Coverage report is generated in `htmlcov/index.html`.

Run specific test file:

```bash
pytest tests/test_checker.py
```

Run specific test:

```bash
pytest tests/test_checker.py::TestPortValidation::test_valid_port
```

### Type Checking

Check for type errors with mypy:

```bash
mypy src tests
```

Mypy is configured to use strict mode for maximum safety.

### Code Quality

#### Linting

Check for code style issues:

```bash
ruff check src tests
```

#### Formatting

Check if code is properly formatted:

```bash
ruff format --check src tests
```

Auto-format code:

```bash
ruff format src tests
```

#### All Checks

Run all quality checks:

```bash
ruff check src tests
ruff format --check src tests
mypy src tests
pytest
```

---

## Project Structure

```text
portreach/
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI/CD
├── src/
│   └── portreach/
│       ├── __init__.py         # Package exports
│       ├── __main__.py         # Module entry point
│       ├── checker.py          # Core port checking logic
│       ├── cli.py              # CLI interface
│       ├── exceptions.py       # Custom exceptions
│       └── models.py           # Result dataclasses
├── tests/
│   ├── conftest.py            # pytest configuration
│   ├── test_checker.py        # Core logic tests
│   └── test_cli.py            # CLI tests
├── test_sanity_check.py       # Quick smoke checks
├── test_manual_scenarios.py   # Functional scenarios
├── verify_release.ps1         # Windows release checks
├── verify_release.sh          # Bash release checks
├── RENAME_REPORT.md           # Rename verification notes
├── .gitignore
├── CHANGELOG.md               # Version history
├── LICENSE                    # MIT License
├── README.md                  # This file
├── TESTING.md                 # Testing instructions
└── pyproject.toml             # Package configuration
```

### Module Overview

**`checker.py`** - Core networking logic
- `validate_port(port)` - Validate port number
- `parse_ports(specs)` - Parse port specifications and ranges
- `check_port(host, port, timeout)` - Check single port
- `check_ports(host, ports, timeout)` - Check multiple ports

**`cli.py`** - Command-line interface
- `create_parser()` - Build argument parser
- `format_port_result()` - Format single port result
- `format_check_result()` - Format multiple ports result
- `main(argv)` - CLI entry point

**`models.py`** - Data types
- `PortResult` - Single port result
- `CheckResult` - Multiple ports result

**`exceptions.py`** - Exception classes
- `PortReachError` - Base exception
- `InvalidPortError` - Invalid port number
- `InvalidRangeError` - Invalid port range
- `InvalidHostError` - Internal hostname-resolution exception; `check_port` returns resolution failures in `PortResult.error`

---

## Contributing

Contributions are welcome! Please follow these guidelines:

### Before Contributing

1. Check [existing issues](https://github.com/dimpletz/portreach/issues)
2. For major changes, open an issue to discuss approach
3. Keep changes focused and minimal

### Code Standards

1. All tests must pass: `pytest`
2. Code must be type-checked: `mypy src tests`
3. Code must pass linting: `ruff check src tests`
4. Code must be formatted: `ruff format src tests`
5. New features should include tests

### Submitting Changes

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Write tests for new functionality
5. Ensure all checks pass
6. Commit with clear message: `git commit -am 'Add feature X'`
7. Push to your fork: `git push origin feature/your-feature`
8. Open a pull request

### What We're Looking For

- Bug reports with reproduction steps
- Performance improvements (with benchmarks)
- Documentation improvements
- Test coverage improvements
- New port checking strategies (if they don't add dependencies)

### What We Won't Accept

- Changes that add external runtime dependencies
- Changes that reduce type safety
- Contributions without tests
- Code that breaks existing functionality

---

## Security and Scope

### What PortReach Is

PortReach is a **connectivity diagnostic utility**. It checks whether TCP ports are reachable using socket connections.

### What PortReach Is NOT

PortReach is **not** a security scanner or penetration testing tool. It does not:

- Perform vulnerability scanning
- Exploit security vulnerabilities
- Conduct stealth scans or evasive techniques
- Test credentials or authentication
- Perform network discovery or subnet scanning
- Conduct aggressive or high-volume scanning
- Fingerprint services or detect versions
- Attempt to exploit services

### Safe Use

PortReach is safe to use on:
- Your own systems
- Servers you own or have permission to test
- Internal networks and services
- Development and testing environments

### Unsafe Use

Do not use PortReach to:
- Scan systems you don't own or haven't been authorized to test
- Violate computer access laws or policies
- Conduct unauthorized security testing
- Test systems in production without proper change management

### Responsible Disclosure

If you discover a security issue in PortReach, report it through [GitHub Issues](https://github.com/dimpletz/portreach/issues) and avoid including sensitive details in a public report.

---

## Roadmap

### Version 0.1.0 (Current)

✓ Single and multiple port checking
✓ Port range support
✓ JSON output
✓ Quiet mode
✓ Configurable timeouts
✓ Hostname resolution
✓ IPv4 and IPv6 support
✓ Clean Python API
✓ Comprehensive test suite
✓ Type annotations throughout

### Potential Future Enhancements

- **v0.2.0 Ideas**:
  - Connection retry logic with exponential backoff
  - Parallel port checking for faster batch operations
  - DNS caching for repeated lookups
  - Performance metrics (connection time)
  - Configuration file support for default settings
  - Shell completion scripts (bash/zsh/PowerShell)
  - Batch mode for checking multiple hosts

- **Future Interfaces**:
  - Web UI for graphical port checking
  - REST API for remote checking
  - MCP (Model Context Protocol) server for AI applications
  - GitHub Action for CI/CD workflows
  - Docker container for isolated checking

### Not Planned

- Vulnerability scanning
- Service fingerprinting
- Aggressive scanning features
- Built-in VPN or proxy support
- Integration with cloud provider APIs

---

## License

PortReach is released under the **MIT License**. See [LICENSE](LICENSE) for details.

This means you can:
- Use PortReach in commercial projects
- Modify the source code
- Distribute PortReach
- Use it privately

As long as you include a copy of the license and don't hold us liable.

---

## Author

**Ofelia B Webb**

For questions or issues, please open an issue on GitHub:
[https://github.com/dimpletz/portreach/issues](https://github.com/dimpletz/portreach/issues)

---

## Acknowledgments

PortReach is built with:
- Python 3.10+
- pytest for testing
- mypy for type checking
- ruff for code quality

---

**Happy port checking! 🚀**
