# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-07

### Added

- Initial release of PortReach
- CLI tool for checking TCP port connectivity
- Support for single port checking: `portreach localhost 8080`
- Support for multiple ports: `portreach localhost 80 443 8080`
- Support for port ranges: `portreach localhost 8000-8010`
- Configurable connection timeout via `--timeout` option
- JSON output format via `--json` flag
- Quiet mode for scripts and CI/CD via `--quiet` flag
- Proper exit codes (0 = all open, 1 = any closed, 2 = error)
- Host validation and DNS resolution
- IPv4 and IPv6 support
- Python API for programmatic use
- Type hints throughout the codebase
- Comprehensive test suite with pytest
- Type checking with mypy configuration
- Code linting and formatting with Ruff
- GitHub Actions CI/CD workflow
- Support for Python 3.10+
- MIT License
- Complete documentation in README

### Features

#### Core Functionality
- TCP port connectivity checking using sockets
- Proper resource cleanup and timeout handling
- Cross-platform support (Windows, macOS, Linux)

#### CLI
- `portreach` console script
- `python -m portreach` module invocation
- Help text: `portreach --help`
- Version display: `portreach --version`

#### Output Formats
- Human-readable format with ✓/✗ indicators
- JSON output for machine parsing
- Quiet mode for automation

#### Validation
- Port number validation (1-65535)
- Port range expansion with bounds checking
- Hostname resolution with error handling
- Malformed argument detection

### Project Structure
- Clean separation of core logic from CLI
- `portreach.checker` module for port checking
- `portreach.cli` module for CLI interface
- `portreach.models` for typed result objects
- `portreach.exceptions` for custom exceptions
- Modern Python packaging with `pyproject.toml`
- pytest configuration for testing
- Comprehensive GitHub Actions workflow

---

[0.1.0]: https://github.com/dimpletz/portreach/releases/tag/v0.1.0
