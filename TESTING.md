# Testing PortReach

This document covers all testing approaches for PortReach v0.1.0.

## Prerequisites

Install PortReach in development mode with test dependencies:

```bash
pip install -e ".[dev]"
```

This installs:
- PortReach in editable mode
- pytest (unit testing)
- ruff (linting/formatting)
- mypy (type checking)
- build (packaging)
- twine (package validation)

## Standard Unit Tests

Run the full pytest suite (60 tests across 2 files):

```bash
pytest
# or with verbose output
pytest -v
```

Listener-based tests use ephemeral port binding. Fixed port values are used only for invalid-input checks.

**Expected**: All 60 tests pass. Runtime depends on the Python version and host.

## Quick Sanity Check

Run `test_sanity_check.py` for a quick 7-test validation:

```bash
python test_sanity_check.py
```

Tests:
- Version flag works and reports correct version
- Help flag produces output
- Invalid port (99999) returns exit code 2
- JSON output format is valid
- Quiet mode suppresses output
- Open port detection with ephemeral socket
- Closed port detection with ephemeral port

**Expected**: 7/7 tests pass.

## Comprehensive Scenario Tests

Run `test_manual_scenarios.py` for detailed functional validation:

```bash
python test_manual_scenarios.py
```

Tests (11 total):
- Open port detection
- Closed port detection
- Multiple ports and range expansion (one scenario function)
- JSON output format
- Quiet mode
- Exit code 0 (all ports open)
- Exit code 1 (any port closed)
- Exit code 2 (configuration error)
- Help flag
- Version flag
- Timeout parameter

Listener-based scenarios use ephemeral local sockets. The timeout scenario uses the reserved TEST-NET address `192.0.2.1`; it does not require a public service, but local routing and firewall behavior can affect its timing.

**Expected**: 11/11 tests pass. Runtime depends on the host.

## Release Verification Scripts

For release validation, run the platform-appropriate script:

### Windows (PowerShell)

```powershell
.\verify_release.ps1
```

**What it checks** (12 checks):
1. Code quality - ruff linting
2. Code formatting - ruff format compliance
3. Type checking - mypy
4. Unit tests - pytest (60 tests)
5. Package build - wheel and source distributions
6. Package validation - twine check
7. Version command works
8. Help command works
9. Open port detection and exit code 0 (ephemeral socket)
10. Closed port detection and exit code 1 (ephemeral socket)
11. Exit code 2 for invalid input
12. Parsed JSON output

**Expected**: All 12 checks pass. The first package build may take longer.

Fails with non-zero exit code if any check fails.

### Linux/macOS (Bash)

```bash
chmod +x verify_release.sh
./verify_release.sh
```

Same checks as PowerShell version.

**Expected**: All 12 checks pass.

Fails with non-zero exit code if any check fails.

## Recommended Test Sequence

### Before Local Commit
```bash
python test_sanity_check.py
```

### Before Pushing to Repository
```bash
python test_manual_scenarios.py
```

### Before Release
```powershell
.\verify_release.ps1
```

```bash
./verify_release.sh
```

## Exit Codes

PortReach uses standard exit codes:

| Code | Meaning | Example |
|------|---------|---------|
| 0 | Success | All ports open |
| 1 | Failure | Any port closed |
| 2 | Error | Invalid arguments (port > 65535, timeout invalid, etc.) |

## Manual Testing Examples

Listener-based examples in the scenario suite allocate ports dynamically. To run only its open-port check:

```bash
python -c "from test_manual_scenarios import test_open_port; test_open_port()"
```

Run `python test_manual_scenarios.py` for the complete set of CLI, output, and exit-code examples without assuming fixed ports are available.

## Full Verification Checklist

For a complete pre-release verification:

```bash
# 1. Code quality checks
ruff check src tests
ruff format --check src tests
mypy src tests

# 2. Unit tests
pytest

# 3. Sanity tests
python test_sanity_check.py

# 4. Comprehensive tests
python test_manual_scenarios.py

# 5. Package build and validation
python -m build
python -m twine check dist/*

```

Run the platform-appropriate release verifier:

```powershell
.\verify_release.ps1
```

```bash
./verify_release.sh
```

## Troubleshooting

### "portreach: command not found"
Install in development mode: `pip install -e ".[dev]"`

### Status symbols fail to print on Windows
Enable Python UTF-8 mode (`PYTHONUTF8=1`) in terminals using a legacy text encoding.

### Ephemeral port tests fail
Verify Python can create sockets: `python -c "import socket; s = socket.socket(); s.bind(('127.0.0.1', 0)); print(s.getsockname()); s.close()"`

### pytest discovery fails
Run `pytest` from the repository root (the directory containing `pyproject.toml`).

### Verification scripts don't run (Linux/macOS)
Make executable: `chmod +x verify_release.sh`

## Test Coverage Summary

These checks cover:

| Component | Tests | Location |
|-----------|-------|----------|
| CLI Interface | 10+ | test_*.py, verify_release.* |
| Port Detection | 8+ | test_*.py, verify_release.* |
| Output Formats | 3+ | test_*.py |
| Exit Codes | 3+ | test_*.py, verify_release.* |
| Error Handling | 2+ | test_*.py |
| Code Quality | 3+ | verify_release.* |
| Package Build | 2+ | verify_release.* |
| Type Safety | 1+ | verify_release.* |

**Total: 30+ automated checks**

## CI/CD Integration

### GitHub Actions

The repository workflow runs lint, formatting, mypy, pytest, and package validation. The following is an optional example for running the smoke suites as additional CI steps:

```yaml
- name: Sanity Check
  run: python test_sanity_check.py

- name: Comprehensive Tests
  run: python test_manual_scenarios.py

- name: Release Verification
  run: ./verify_release.sh
```

### GitLab CI

```yaml
test:
  script:
    - python test_sanity_check.py
    - python test_manual_scenarios.py
    - ./verify_release.sh
```

## Important Notes

- **Listener checks use local ephemeral sockets** — They do not need a public service
- **Fixed ports are not used for listener state** — Invalid-input tests intentionally use fixed invalid values
- **Deterministic listener checks** — Local open/closed-port tests use allocated sockets
- **Timeout test target** — The manual suite attempts the reserved TEST-NET address `192.0.2.1`; it needs no public service but routing and firewall settings can affect timing
- **Non-destructive** — Tests create and clean up their own resources
- **Fast execution** — Complete suite runs in <1 minute

## Files

- `test_sanity_check.py` — Quick 7-test validation
- `test_manual_scenarios.py` — Comprehensive 11-test suite
- `verify_release.ps1` — Full validation for Windows
- `verify_release.sh` — Full validation for Linux/macOS
- `tests/` — Standard pytest suite (60 tests)

All listener-state checks follow these principles:
- Use local resources
- Use ephemeral ports for listener state; invalid-input tests intentionally use fixed invalid values
- Return proper exit codes
- Clean up after themselves
