"""Tests for configuration loading."""

import tempfile
from pathlib import Path

import pytest

from mkdocs_external_emojis.config import ConfigError, load_config


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_valid_config(self) -> None:
        """Test loading valid configuration."""
        config_content = """
[[providers]]
type = "slack"
namespace = "slack"
token_env = "SLACK_TOKEN"
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(config_content)
            f.flush()

            config = load_config(f.name)

            assert len(config.providers) == 1
            assert config.providers[0].namespace == "slack"
            assert config.providers[0].token_env == "SLACK_TOKEN"

            Path(f.name).unlink()

    def test_missing_config_file(self) -> None:
        """Test error when config file doesn't exist."""
        with pytest.raises(ConfigError, match="not found"):
            load_config("nonexistent.toml")

    def test_invalid_toml_syntax(self) -> None:
        """Test error with invalid TOML syntax."""
        config_content = """
[invalid toml syntax
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(config_content)
            f.flush()

            with pytest.raises(ConfigError, match="Invalid TOML"):
                load_config(f.name)

            Path(f.name).unlink()

    def test_missing_providers(self) -> None:
        """Test error when no providers configured."""
        config_content = """
[cache]
directory = ".cache"
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(config_content)
            f.flush()

            with pytest.raises(ConfigError, match="at least one"):
                load_config(f.name)

            Path(f.name).unlink()

    def test_config_with_filters(self) -> None:
        """Test loading config with emoji filters."""
        config_content = """
[[providers]]
type = "slack"
namespace = "slack"
token_env = "SLACK_TOKEN"

[providers.filters]
include_patterns = ["party*", "cat*"]
exclude_patterns = ["*-old"]
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(config_content)
            f.flush()

            config = load_config(f.name)

            assert config.providers[0].filters.include_patterns == ["party*", "cat*"]
            assert config.providers[0].filters.exclude_patterns == ["*-old"]

            Path(f.name).unlink()

    def test_multiple_providers(self) -> None:
        """Test loading config with multiple providers."""
        config_content = """
[[providers]]
type = "slack"
namespace = "slack1"
token_env = "SLACK_TOKEN_1"

[[providers]]
type = "slack"
namespace = "slack2"
token_env = "SLACK_TOKEN_2"
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(config_content)
            f.flush()

            config = load_config(f.name)

            assert len(config.providers) == 2
            assert config.providers[0].namespace == "slack1"
            assert config.providers[1].namespace == "slack2"

            Path(f.name).unlink()
