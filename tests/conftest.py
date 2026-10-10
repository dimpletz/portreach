"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture(autouse=True)
def reset_socket_timeout():
    """Ensure socket timeout is reset after each test."""
    yield
    # Cleanup if needed
