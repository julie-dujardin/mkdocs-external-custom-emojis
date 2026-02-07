"""Pytest configuration and shared fixtures."""

import pytest


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    """Clean environment variables for each test."""
    # Remove common token env vars
    for var in ["SLACK_TOKEN", "WORK_SLACK_TOKEN", "DISCORD_TOKEN", "DISCORD_GUILD_ID"]:
        monkeypatch.delenv(var, raising=False)
