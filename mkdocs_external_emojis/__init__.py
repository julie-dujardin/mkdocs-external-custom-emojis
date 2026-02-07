"""MkDocs plugin to sync custom emojis from external providers."""

from mkdocs_external_emojis.config import ConfigError, load_config
from mkdocs_external_emojis.models import (
    EmojiConfig,
    EmojiFormat,
    EmojiInfo,
    ProviderConfig,
    ProviderType,
)

__version__ = "0.1.0"

__all__ = [
    "ConfigError",
    "EmojiConfig",
    "EmojiFormat",
    "EmojiInfo",
    "ProviderConfig",
    "ProviderType",
    "load_config",
]
