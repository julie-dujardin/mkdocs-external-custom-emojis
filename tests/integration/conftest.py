"""Pytest configuration for integration tests."""

import os

import pytest

REQUIRED_SECRETS = ["SLACK_TOKEN", "DISCORD_BOT_TOKEN", "DISCORD_GUILD_ID"]


def secrets_available() -> bool:
    """Check if all required secrets are available."""
    return all(os.environ.get(var) for var in REQUIRED_SECRETS)


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "integration: marks tests as integration tests")


def pytest_collection_modifyitems(config, items):
    """Skip integration tests if secrets are not available."""
    if secrets_available():
        return

    skip_marker = pytest.mark.skip(reason="Integration test secrets not available")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_marker)


@pytest.fixture(scope="module")
def project_root():
    """Return the project root directory."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
