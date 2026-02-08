"""MkDocs plugin to sync custom emojis from external providers."""

from mkdocs_external_emojis.config import ConfigError, load_config
from mkdocs_external_emojis.constants import DEFAULT_CONFIG_FILE, LOGGER_NAME
from mkdocs_external_emojis.models import (
    EmojiConfig,
    EmojiFormat,
    EmojiInfo,
    ProviderConfig,
    ProviderType,
)

__version__ = "0.3.2"

__all__ = [
    "DEFAULT_CONFIG_FILE",
    "LOGGER_NAME",
    "ConfigError",
    "EmojiConfig",
    "EmojiFormat",
    "EmojiInfo",
    "ProviderConfig",
    "ProviderType",
    "load_config",
]
