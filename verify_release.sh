#!/usr/bin/env bash
set -Eeuo pipefail

TESTS_PASSED=0
TESTS_FAILED=0
LISTENER_PID=""
LISTENER_FILE=""
COMMAND_OUTPUT=""

cleanup() {
    if [[ -n "$LISTENER_PID" ]]; then
        kill "$LISTENER_PID" 2>/dev/null || true
        wait "$LISTENER_PID" 2>/dev/null || true
        LISTENER_PID=""
    fi
    if [[ -n "$LISTENER_FILE" ]]; then
        rm -f "$LISTENER_FILE"
        LISTENER_FILE=""
    fi
}
trap cleanup EXIT

run_checked() {
    local expected_status="$1"
    shift
    local output
    local actual_status

    if output=$("$@" 2>&1); then
        actual_status=0
    else
        actual_status=$?
    fi
    COMMAND_OUTPUT="$output"
    if [[ "$actual_status" -ne "$expected_status" ]]; then
        printf 'Command failed (expected %s, got %s): %s\n%s\n' \
            "$expected_status" "$actual_status" "$*" "$output" >&2
        return 1
    fi
}

run_step() {
    local name="$1"
    shift
    printf '\n[TEST] %s\n' "$name"
    if "$@"; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        printf '[PASS] %s\n' "$name"
    else
        local status=$?
        TESTS_FAILED=$((TESTS_FAILED + 1))
        printf '[FAIL] %s (status %s)\n' "$name" "$status" >&2
    fi
}

check_ruff() {
    run_checked 0 ruff check src tests
}

check_format() {
    run_checked 0 ruff format --check src tests
}

check_mypy() {
    run_checked 0 mypy src tests
}

check_unit_tests() {
    run_checked 0 python -m pytest tests -q
}

check_build() {
    if ! rm -rf build dist src/portreach.egg-info; then
        printf 'Could not remove previous build artifacts\n' >&2
        return 1
    fi
    run_checked 0 python -m build || return 1
    [[ -f dist/portreach-0.1.0.tar.gz ]] || {
        printf 'Missing sdist: dist/portreach-0.1.0.tar.gz\n' >&2
        return 1
    }
    [[ -f dist/portreach-0.1.0-py3-none-any.whl ]] || {
        printf 'Missing wheel: dist/portreach-0.1.0-py3-none-any.whl\n' >&2
        return 1
    }
}

check_twine() {
    [[ -f dist/portreach-0.1.0.tar.gz && -f dist/portreach-0.1.0-py3-none-any.whl ]] || {
        printf 'Expected package artifacts are missing\n' >&2
        return 1
    }
    run_checked 0 python -m twine check \
        dist/portreach-0.1.0.tar.gz \
        dist/portreach-0.1.0-py3-none-any.whl
}

check_version() {
    run_checked 0 python -m portreach --version || return 1
    [[ "$COMMAND_OUTPUT" == "portreach 0.1.0" ]]
}

check_help() {
    run_checked 0 python -m portreach --help || return 1
    [[ "$COMMAND_OUTPUT" == *"usage: portreach"* ]]
}

start_listener() {
    if ! LISTENER_FILE=$(mktemp); then
        printf 'Could not create listener port file\n' >&2
        return 1
    fi
    python -c 'import socket,time; s=socket.socket(); s.bind(("127.0.0.1", 0)); s.listen(1); print(s.getsockname()[1], flush=True); time.sleep(60)' \
        >"$LISTENER_FILE" 2>&1 &
    LISTENER_PID=$!

    local attempts=0
    while [[ ! -s "$LISTENER_FILE" && "$attempts" -lt 100 ]]; do
        if ! kill -0 "$LISTENER_PID" 2>/dev/null; then
            cat "$LISTENER_FILE" >&2
            stop_listener
            return 1
        fi
        if ! sleep 0.05; then
            printf 'Could not wait for loopback listener startup\n' >&2
            stop_listener
            return 1
        fi
        attempts=$((attempts + 1))
    done
    if [[ ! -s "$LISTENER_FILE" ]]; then
        printf 'Timed out starting loopback listener\n' >&2
        stop_listener
        return 1
    fi
    LISTENER_PORT=$(<"$LISTENER_FILE")
}

stop_listener() {
    if [[ -n "$LISTENER_PID" ]]; then
        kill "$LISTENER_PID" 2>/dev/null || true
        wait "$LISTENER_PID" 2>/dev/null || true
        LISTENER_PID=""
    fi
    if [[ -n "$LISTENER_FILE" ]]; then
        rm -f "$LISTENER_FILE"
        LISTENER_FILE=""
    fi
}

check_open_port() {
    local port
    start_listener || return 1
    port="$LISTENER_PORT"
    run_checked 0 python -m portreach 127.0.0.1 "$port" --quiet
    local status=$?
    stop_listener
    return "$status"
}

check_closed_port() {
    local output
    local port
    if output=$(python -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1]); s.close()' 2>&1); then
        port="$output"
    else
        local status=$?
        printf 'Could not reserve a closed-port candidate: %s\n' "$output" >&2
        return "$status"
    fi
    run_checked 1 python -m portreach 127.0.0.1 "$port" --quiet
}

check_invalid_input() {
    run_checked 2 python -m portreach 127.0.0.1 99999 --quiet
}

check_json() {
    local port
    start_listener || return 1
    port="$LISTENER_PORT"
    if run_checked 0 python -m portreach 127.0.0.1 "$port" --json; then
        python -c 'import json,sys; data=json.load(sys.stdin); assert data["host"] == "127.0.0.1" and len(data["results"]) == 1 and data["results"][0]["status"] == "open"' <<<"$COMMAND_OUTPUT"
        local status=$?
        stop_listener
        return "$status"
    fi
    local status=$?
    stop_listener
    return "$status"
}

printf 'PortReach v0.1.0 - Release Verification\n'
run_step "Ruff lint" check_ruff
run_step "Ruff format" check_format
run_step "Mypy" check_mypy
run_step "Unit tests" check_unit_tests
run_step "Clean package build" check_build
run_step "Twine validation" check_twine
run_step "Version command" check_version
run_step "Help command" check_help
run_step "Open loopback port (exit 0)" check_open_port
run_step "Closed loopback port (exit 1)" check_closed_port
run_step "Invalid port (exit 2)" check_invalid_input
run_step "JSON output parses" check_json

printf '\nRelease verification: %s passed, %s failed, %s total\n' \
    "$TESTS_PASSED" "$TESTS_FAILED" "$((TESTS_PASSED + TESTS_FAILED))"
if [[ "$TESTS_FAILED" -gt 0 ]]; then
    exit 1
fi
exit 0
