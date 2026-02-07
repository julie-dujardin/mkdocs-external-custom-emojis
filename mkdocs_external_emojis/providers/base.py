"""Abstract base class for emoji providers."""

import fnmatch
from abc import ABC, abstractmethod

from mkdocs_external_emojis.models import EmojiInfo, ProviderConfig


class ProviderError(Exception):
    """Provider-specific error."""

    pass


class AbstractEmojiProvider(ABC):
    """Abstract base class for emoji providers."""

    def __init__(self, config: ProviderConfig) -> None:
        """
        Initialize the provider.

        Args:
            config: Provider configuration
        """
        self.config = config

    @abstractmethod
    def fetch_emojis(self) -> dict[str, EmojiInfo]:
        """
        Fetch all available emojis from the provider.

        Returns:
            Dictionary mapping emoji names to EmojiInfo objects

        Raises:
            ProviderError: If fetching fails
        """
        pass

    @abstractmethod
    def validate_config(self) -> int:
        """
        Validate provider-specific configuration.

        Returns:
            Number of emojis available from the provider

        Raises:
            ProviderError: If configuration is invalid
        """
        pass

    @abstractmethod
    def get_required_env_vars(self) -> list[str]:
        """
        Get list of required environment variable names.

        Returns:
            List of environment variable names
        """
        pass

    def filter_emojis(self, emojis: dict[str, EmojiInfo]) -> dict[str, EmojiInfo]:
        """
        Filter emojis based on include/exclude patterns.

        Args:
            emojis: Dictionary of all emojis

        Returns:
            Filtered dictionary of emojis
        """
        if not self.config.filters.include_patterns and not self.config.filters.exclude_patterns:
            return emojis

        filtered: dict[str, EmojiInfo] = {}

        for name, emoji in emojis.items():
            # Check exclude patterns first
            if self.config.filters.exclude_patterns and any(
                fnmatch.fnmatch(name, pattern) for pattern in self.config.filters.exclude_patterns
            ):
                continue

            # Check include patterns
            if self.config.filters.include_patterns and not any(
                fnmatch.fnmatch(name, pattern) for pattern in self.config.filters.include_patterns
            ):
                continue

            filtered[name] = emoji

        return filtered

    def resolve_aliases(self, emojis: dict[str, EmojiInfo]) -> dict[str, EmojiInfo]:
        """
        Resolve emoji aliases to their target emojis.

        Args:
            emojis: Dictionary of emojis (including aliases)

        Returns:
            Dictionary with aliases resolved (pointing to same URL as target)
        """
        resolved: dict[str, EmojiInfo] = {}

        # First pass: add non-aliases
        for name, emoji in emojis.items():
            if not emoji.is_alias:
                resolved[name] = emoji

        # Second pass: resolve aliases
        max_depth = 10  # Prevent infinite loops
        for name, emoji in emojis.items():
            if emoji.is_alias and emoji.alias_of:
                target = emoji.alias_of
                depth = 0

                # Follow the alias chain
                while target in emojis and emojis[target].is_alias and depth < max_depth:
                    next_target = emojis[target].alias_of
                    if next_target is None:
                        break
                    target = next_target
                    depth += 1

                # Get the final target emoji
                if target in resolved:
                    target_emoji = resolved[target]
                    # Create a copy with the alias name
                    resolved[name] = EmojiInfo(
                        name=name,
                        url=target_emoji.url,
                        format=target_emoji.format,
                    )

        return resolved
