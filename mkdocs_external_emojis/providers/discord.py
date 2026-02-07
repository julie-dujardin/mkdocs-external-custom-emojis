"""Discord emoji provider implementation."""

import os

import requests

from mkdocs_external_emojis.models import EmojiInfo, ProviderConfig
from mkdocs_external_emojis.providers.base import AbstractEmojiProvider, ProviderError


class DiscordEmojiProvider(AbstractEmojiProvider):
    """Provider for fetching custom emojis from a Discord guild."""

    API_BASE = "https://discord.com/api/v10"
    CDN_BASE = "https://cdn.discordapp.com/emojis"

    def __init__(self, config: ProviderConfig) -> None:
        """
        Initialize Discord provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)
        self.token = os.getenv(config.token_env)

        if not self.token:
            raise ProviderError(
                f"Discord token not found in environment variable: {config.token_env}"
            )

        if not config.tenant_id:
            raise ProviderError(
                "tenant_id (guild/server ID env var) is required for Discord provider"
            )

        self.guild_id = os.getenv(config.tenant_id)
        if not self.guild_id:
            raise ProviderError(
                f"Discord guild ID not found in environment variable: {config.tenant_id}"
            )

    def fetch_emojis(self) -> dict[str, EmojiInfo]:
        """
        Fetch all custom emojis from Discord guild.

        Returns:
            Dictionary mapping emoji names to EmojiInfo objects

        Raises:
            ProviderError: If API request fails
        """
        headers = {
            "Authorization": f"Bot {self.token}",
        }

        url = f"{self.API_BASE}/guilds/{self.guild_id}/emojis"

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ProviderError(f"Failed to fetch emojis from Discord: {e}") from e

        data = response.json()

        if isinstance(data, dict) and "message" in data:
            raise ProviderError(f"Discord API error: {data['message']}")

        emojis: dict[str, EmojiInfo] = {}

        for emoji_data in data:
            name = emoji_data.get("name")
            emoji_id = emoji_data.get("id")
            animated = emoji_data.get("animated", False)

            if not name or not emoji_id:
                continue

            extension = "gif" if animated else "png"
            url = f"{self.CDN_BASE}/{emoji_id}.{extension}"

            emojis[name] = EmojiInfo.from_url(name, url)

        emojis = self.filter_emojis(emojis)

        return emojis

    def validate_config(self) -> int:
        """
        Validate Discord provider configuration.

        Returns:
            Number of emojis available in the guild

        Raises:
            ProviderError: If configuration is invalid or token lacks permissions
        """
        if not self.config.token_env:
            raise ProviderError("token_env is required for Discord provider")

        if not self.config.tenant_id:
            raise ProviderError("tenant_id is required for Discord provider")

        headers = {
            "Authorization": f"Bot {self.token}",
        }

        url = f"{self.API_BASE}/guilds/{self.guild_id}/emojis"

        try:
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 401:
                raise ProviderError("Invalid Discord token")

            if response.status_code == 403:
                raise ProviderError(
                    "Bot lacks permission to access guild emojis. "
                    "Ensure the bot has the 'Manage Emojis and Stickers' permission."
                )

            if response.status_code == 404:
                raise ProviderError(
                    f"Guild not found: {self.guild_id}. Ensure the bot is a member of the guild."
                )

            response.raise_for_status()
            data = response.json()

            return len(data)

        except requests.exceptions.RequestException as e:
            raise ProviderError(f"Failed to validate Discord configuration: {e}") from e

    def get_required_env_vars(self) -> list[str]:
        """
        Get list of required environment variable names.

        Returns:
            List containing the token and tenant ID environment variable names
        """
        env_vars = [self.config.token_env]
        if self.config.tenant_id:
            env_vars.append(self.config.tenant_id)
        return env_vars
