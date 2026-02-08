"""Tests for CLI commands."""

import pytest
from click.testing import CliRunner

from mkdocs_external_emojis.cli import cache, init, main, sync, validate


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()


@pytest.fixture
def valid_config_file(tmp_path):
    """Create a valid config file."""
    config_content = """
[[providers]]
type = "slack"
namespace = "slack"
token_env = "SLACK_TOKEN"
enabled = true
"""
    config_file = tmp_path / "emoji-config.toml"
    config_file.write_text(config_content)
    return config_file


class TestMain:
    """Tests for main CLI group."""

    def test_version(self, runner):
        """Test --version flag."""
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.3.1" in result.output

    def test_help(self, runner):
        """Test --help flag."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Manage custom emojis" in result.output


class TestInit:
    """Tests for init command."""

    def test_init_creates_config(self, runner, tmp_path):
        """Test init creates a config file."""
        config_path = tmp_path / "emoji-config.toml"
        result = runner.invoke(init, [str(config_path)])

        assert result.exit_code == 0
        assert "Created configuration file" in result.output
        assert config_path.exists()

    def test_init_fails_if_exists(self, runner, valid_config_file):
        """Test init fails if config already exists."""
        result = runner.invoke(init, [str(valid_config_file)])

        assert result.exit_code == 1
        assert "already exists" in result.output


class TestValidate:
    """Tests for validate command."""

    def test_validate_valid_config(self, runner, valid_config_file):
        """Test validate with valid config."""
        result = runner.invoke(validate, ["--config", str(valid_config_file)])

        assert result.exit_code == 0
        assert "Configuration file is valid" in result.output
        assert "1 enabled provider" in result.output

    def test_validate_missing_config(self, runner, tmp_path):
        """Test validate with missing config."""
        missing_path = tmp_path / "nonexistent.toml"
        result = runner.invoke(validate, ["--config", str(missing_path)])

        assert result.exit_code == 1
        assert "not found" in result.output

    def test_validate_check_env_missing(self, runner, valid_config_file):
        """Test validate --check-env when env vars missing."""
        result = runner.invoke(validate, ["--config", str(valid_config_file), "--check-env"])

        assert result.exit_code == 1
        assert "Missing variables" in result.output


class TestCache:
    """Tests for cache command."""

    def test_cache_shows_info(self, runner, valid_config_file, monkeypatch):
        """Test cache command shows cache info."""
        monkeypatch.setenv("SLACK_TOKEN", "xoxb-test-token")
        result = runner.invoke(cache, ["--config", str(valid_config_file)])

        assert result.exit_code == 0
        assert "slack:" in result.output
        assert "Files:" in result.output


class TestSync:
    """Tests for sync command."""

    def test_sync_missing_env(self, runner, valid_config_file):
        """Test sync fails when env vars missing."""
        result = runner.invoke(sync, ["--config", str(valid_config_file)])

        assert result.exit_code == 1
        assert "Missing environment variables" in result.output

    def test_sync_dry_run(self, runner, valid_config_file, monkeypatch):
        """Test sync --dry-run shows what would be done."""
        monkeypatch.setenv("SLACK_TOKEN", "xoxb-test-token")
        result = runner.invoke(sync, ["--config", str(valid_config_file), "--dry-run"])

        assert result.exit_code == 0
        assert "DRY RUN" in result.output

    def test_sync_nonexistent_provider(self, runner, valid_config_file, monkeypatch):
        """Test sync with non-existent provider filter."""
        monkeypatch.setenv("SLACK_TOKEN", "xoxb-test-token")
        result = runner.invoke(
            sync, ["--config", str(valid_config_file), "--provider", "nonexistent"]
        )

        assert result.exit_code == 1
        assert "not found" in result.output
