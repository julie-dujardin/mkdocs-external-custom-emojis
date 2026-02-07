"""Slack emoji provider implementation."""

import os

import requests

from mkdocs_external_emojis.models import EmojiInfo, ProviderConfig
from mkdocs_external_emojis.providers.base import AbstractEmojiProvider, ProviderError


class SlackEmojiProvider(AbstractEmojiProvider):
    """Provider for fetching custom emojis from Slack."""

    API_URL = "https://slack.com/api/emoji.list"

    def __init__(self, config: ProviderConfig) -> None:
        """
        Initialize Slack provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)
        self.token = os.getenv(config.token_env)

        if not self.token:
            raise ProviderError(
                f"Slack token not found in environment variable: {config.token_env}"
            )

    def fetch_emojis(self) -> dict[str, EmojiInfo]:
        """
        Fetch all custom emojis from Slack workspace.

        Returns:
            Dictionary mapping emoji names to EmojiInfo objects

        Raises:
            ProviderError: If API request fails
        """
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.get(self.API_URL, headers=headers, timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ProviderError(f"Failed to fetch emojis from Slack: {e}") from e

        data = response.json()

        if not data.get("ok"):
            error = data.get("error", "Unknown error")
            raise ProviderError(f"Slack API error: {error}")

        emoji_data: dict[str, str] = data.get("emoji", {})
        emojis: dict[str, EmojiInfo] = {}

        # Parse emoji data
        for name, value in emoji_data.items():
            if value.startswith("alias:"):
                # This is an alias
                target = value.replace("alias:", "")
                emojis[name] = EmojiInfo.from_alias(name, target)
            else:
                # This is a regular emoji with a URL
                emojis[name] = EmojiInfo.from_url(name, value)

        # Filter emojis based on patterns
        emojis = self.filter_emojis(emojis)

        # Resolve aliases to actual URLs
        emojis = self.resolve_aliases(emojis)

        return emojis

    def validate_config(self) -> int:
        """
        Validate Slack provider configuration.

        Returns:
            Number of emojis available in the workspace

        Raises:
            ProviderError: If configuration is invalid or token lacks permissions
        """
        if not self.config.token_env:
            raise ProviderError("token_env is required for Slack provider")

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        # Test the token by making a simple API call
        try:
            response = requests.get(
                "https://slack.com/api/auth.test",
                headers=headers,
                timeout=10,
            )
            data = response.json()

            if not data.get("ok"):
                error = data.get("error", "Unknown error")
                raise ProviderError(f"Invalid Slack token: {error}")

        except requests.exceptions.RequestException as e:
            raise ProviderError(f"Failed to validate Slack token: {e}") from e

        # Verify emoji:read permission by fetching emoji list
        try:
            response = requests.get(self.API_URL, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            if not data.get("ok"):
                error = data.get("error", "Unknown error")
                raise ProviderError(
                    f"Token lacks emoji:read permission: {error}"
                )

            emoji_count = len(data.get("emoji", {}))
            return emoji_count

        except requests.exceptions.RequestException as e:
            raise ProviderError(f"Failed to verify emoji permissions: {e}") from e

    def get_required_env_vars(self) -> list[str]:
        """
        Get list of required environment variable names.

        Returns:
            List containing the token environment variable name
        """
        return [self.config.token_env]
