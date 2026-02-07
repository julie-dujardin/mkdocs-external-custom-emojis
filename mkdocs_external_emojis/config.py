"""Configuration loading and validation."""

import os
import tomllib
import warnings
from pathlib import Path

from mkdocs_external_emojis.constants import DEFAULT_CONFIG_FILE
from mkdocs_external_emojis.models import EmojiConfig, ProviderConfig


class ConfigError(Exception):
    """Configuration error."""

    pass


def load_config(config_path: Path | str = DEFAULT_CONFIG_FILE) -> EmojiConfig:
    """
    Load emoji configuration from TOML file.

    Args:
        config_path: Path to the TOML configuration file

    Returns:
        Parsed and validated EmojiConfig

    Raises:
        ConfigError: If config file is invalid or missing
    """
    config_file = Path(config_path)

    if not config_file.exists():
        raise ConfigError(f"Configuration file not found: {config_file}")

    try:
        with open(config_file, "rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"Invalid TOML syntax in {config_file}: {e}") from e
    except Exception as e:
        raise ConfigError(f"Failed to read {config_file}: {e}") from e

    # Validate required fields
    if "providers" not in data:
        raise ConfigError("Configuration must include at least one [[providers]] entry")

    if not isinstance(data["providers"], list) or len(data["providers"]) == 0:
        raise ConfigError("At least one provider must be configured")

    try:
        config = EmojiConfig(**data)
    except (TypeError, ValueError) as e:
        raise ConfigError(f"Invalid configuration: {e}") from e

    # Validate each provider
    for provider in config.providers:
        _validate_provider(provider)

    return config


def _validate_provider(provider: ProviderConfig) -> None:
    """
    Validate a provider configuration.

    Args:
        provider: Provider configuration to validate

    Raises:
        ConfigError: If provider config is invalid
    """
    # Check namespace is valid (alphanumeric, dashes, underscores)
    namespace = provider.namespace
    if not namespace:
        raise ConfigError("Namespace cannot be empty")
    if len(namespace) > 64:
        raise ConfigError(f"Namespace '{namespace}' is too long (max 64 characters)")
    if not namespace.replace("-", "").replace("_", "").isalnum():
        raise ConfigError(
            f"Invalid namespace '{namespace}': "
            "must contain only alphanumeric characters, dashes, and underscores"
        )

    # Check environment variable name is valid
    if not provider.token_env:
        raise ConfigError(f"Provider '{provider.namespace}' missing token_env")

    # Check if environment variable exists (warning, not error)
    if not os.getenv(provider.token_env):
        warnings.warn(
            f"Environment variable '{provider.token_env}' not set for "
            f"provider '{provider.namespace}'. The build will fail if this "
            f"provider is enabled.",
            UserWarning,
            stacklevel=2,
        )


def validate_environment(config: EmojiConfig) -> list[str]:
    """
    Validate that all required environment variables are set.

    Args:
        config: Emoji configuration to validate

    Returns:
        List of missing environment variable names
    """
    missing = []
    for provider in config.get_enabled_providers():
        if not os.getenv(provider.token_env):
            missing.append(provider.token_env)
    return missing


def create_default_config(path: Path | str = DEFAULT_CONFIG_FILE) -> None:
    """
    Create a default configuration file.

    Args:
        path: Path where to create the config file
    """
    default_config = """# Emoji configuration for mkdocs-external-custom-emojis

# Cache configuration
[cache]
directory = ".mkdocs_emoji_cache"  # Where to store downloaded emojis
ttl_hours = 24                     # Re-fetch after 24 hours
clean_on_build = false             # Whether to clean cache before each build

# Global emoji options
[emojis]
namespace_prefix_required = false  # If true, only :<namespace>-<emoji>: works
max_size_kb = 500                  # Skip emojis larger than this
download_timeout = 30              # Request timeout in seconds

# Slack provider
[[providers]]
type = "slack"
namespace = "slack"                # Emojis will be :slack-emoji-name:
token_env = "SLACK_TOKEN"          # Environment variable name
enabled = true

# Optional: Filter emojis
# [providers.filters]
# include_patterns = ["party*", "cat*"]  # Only sync matching emojis
# exclude_patterns = ["*-old"]           # Skip matching emojis

# Discord provider example:
# [[providers]]
# type = "discord"
# namespace = "discord"                # Emojis will be :discord-emoji-name:
# token_env = "DISCORD_BOT_TOKEN"      # Bot token environment variable
# tenant_id = "DISCORD_GUILD_ID"       # Guild/server ID environment variable
# enabled = true
"""

    config_file = Path(path)
    if config_file.exists():
        raise ConfigError(f"Configuration file already exists: {config_file}")

    config_file.write_text(default_config)
