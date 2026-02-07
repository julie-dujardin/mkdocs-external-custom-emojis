"""Emoji provider implementations."""

from mkdocs_external_emojis.models import ProviderConfig, ProviderType
from mkdocs_external_emojis.providers.base import AbstractEmojiProvider, ProviderError
from mkdocs_external_emojis.providers.discord import DiscordEmojiProvider
from mkdocs_external_emojis.providers.slack import SlackEmojiProvider

# Registry mapping provider types to their implementation classes
PROVIDER_REGISTRY: dict[ProviderType, type[AbstractEmojiProvider]] = {
    ProviderType.SLACK: SlackEmojiProvider,
    ProviderType.DISCORD: DiscordEmojiProvider,
}


def create_provider(config: ProviderConfig) -> AbstractEmojiProvider:
    """
    Create a provider instance from configuration.

    Args:
        config: Provider configuration

    Returns:
        Provider instance

    Raises:
        ProviderError: If provider type is unsupported
    """
    provider_class = PROVIDER_REGISTRY.get(config.type)
    if not provider_class:
        raise ProviderError(f"Unsupported provider type: {config.type}")
    return provider_class(config)


__all__ = [
    "PROVIDER_REGISTRY",
    "AbstractEmojiProvider",
    "DiscordEmojiProvider",
    "ProviderError",
    "SlackEmojiProvider",
    "create_provider",
]
