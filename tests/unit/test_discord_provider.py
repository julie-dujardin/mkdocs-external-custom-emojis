"""Tests for Discord emoji provider."""

import os
from unittest.mock import patch

import pytest
import requests
import requests_mock

from mkdocs_external_emojis.models import ProviderConfig, ProviderType
from mkdocs_external_emojis.providers import DiscordEmojiProvider, ProviderError


class TestDiscordEmojiProvider:
    """Tests for DiscordEmojiProvider."""

    @pytest.fixture
    def provider_config(self) -> ProviderConfig:
        """Create test provider configuration."""
        return ProviderConfig(
            type=ProviderType.DISCORD,
            namespace="discord",
            token_env="DISCORD_TOKEN",
            tenant_id="DISCORD_GUILD_ID",
        )

    @pytest.fixture
    def discord_api_response(self) -> list:
        """Mock Discord API response."""
        return [
            {"id": "123456789", "name": "partyparrot", "animated": True},
            {"id": "987654321", "name": "catjam", "animated": True},
            {"id": "111222333", "name": "thumbsup", "animated": False},
        ]

    def test_initialization_without_token(self, provider_config: ProviderConfig) -> None:
        """Test that initialization fails without token."""
        with pytest.raises(ProviderError, match="not found in environment"):
            DiscordEmojiProvider(provider_config)

    def test_initialization_without_guild_id(self) -> None:
        """Test that initialization fails without guild ID."""
        config = ProviderConfig(
            type=ProviderType.DISCORD,
            namespace="discord",
            token_env="DISCORD_TOKEN",
            tenant_id="DISCORD_GUILD_ID",
        )
        with (
            patch.dict(os.environ, {"DISCORD_TOKEN": "test-token"}),
            pytest.raises(ProviderError, match="guild ID not found"),
        ):
            DiscordEmojiProvider(config)

    def test_initialization_without_tenant_id_config(self) -> None:
        """Test that initialization fails when tenant_id is not configured."""
        config = ProviderConfig(
            type=ProviderType.DISCORD,
            namespace="discord",
            token_env="DISCORD_TOKEN",
            tenant_id=None,
        )
        with (
            patch.dict(os.environ, {"DISCORD_TOKEN": "test-token"}),
            pytest.raises(ProviderError, match=r"tenant_id.*is required"),
        ):
            DiscordEmojiProvider(config)

    def test_initialization_with_token_and_guild(self, provider_config: ProviderConfig) -> None:
        """Test successful initialization with token and guild ID."""
        with patch.dict(os.environ, {"DISCORD_TOKEN": "test-token", "DISCORD_GUILD_ID": "123456"}):
            provider = DiscordEmojiProvider(provider_config)
            assert provider.token == "test-token"
            assert provider.guild_id == "123456"

    def test_fetch_emojis_success(
        self,
        provider_config: ProviderConfig,
        discord_api_response: list,
    ) -> None:
        """Test successful emoji fetching."""
        with patch.dict(os.environ, {"DISCORD_TOKEN": "test-token", "DISCORD_GUILD_ID": "123456"}):
            provider = DiscordEmojiProvider(provider_config)

            with requests_mock.Mocker() as m:
                m.get(
                    "https://discord.com/api/v10/guilds/123456/emojis",
                    json=discord_api_response,
                )

                emojis = provider.fetch_emojis()

                assert len(emojis) == 3
                assert "partyparrot" in emojis
                assert "catjam" in emojis
                assert "thumbsup" in emojis

                # Check animated emoji URL
                assert (
                    emojis["partyparrot"].url == "https://cdn.discordapp.com/emojis/123456789.gif"
                )

                # Check static emoji URL
                assert emojis["thumbsup"].url == "https://cdn.discordapp.com/emojis/111222333.png"

    def test_fetch_emojis_api_error(self, provider_config: ProviderConfig) -> None:
        """Test handling of API errors."""
        with patch.dict(os.environ, {"DISCORD_TOKEN": "test-token", "DISCORD_GUILD_ID": "123456"}):
            provider = DiscordEmojiProvider(provider_config)

            with requests_mock.Mocker() as m:
                m.get(
                    "https://discord.com/api/v10/guilds/123456/emojis",
                    json={"message": "Unknown Guild", "code": 10004},
                )

                with pytest.raises(ProviderError, match="Unknown Guild"):
                    provider.fetch_emojis()

    def test_fetch_emojis_network_error(self, provider_config: ProviderConfig) -> None:
        """Test handling of network errors."""
        with patch.dict(os.environ, {"DISCORD_TOKEN": "test-token", "DISCORD_GUILD_ID": "123456"}):
            provider = DiscordEmojiProvider(provider_config)

            with requests_mock.Mocker() as m:
                m.get(
                    "https://discord.com/api/v10/guilds/123456/emojis",
                    exc=requests.exceptions.ConnectTimeout,
                )

                with pytest.raises(ProviderError, match="Failed to fetch"):
                    provider.fetch_emojis()

    def test_fetch_emojis_skips_incomplete(self, provider_config: ProviderConfig) -> None:
        """Test that emojis without name or id are skipped."""
        with patch.dict(os.environ, {"DISCORD_TOKEN": "test-token", "DISCORD_GUILD_ID": "123456"}):
            provider = DiscordEmojiProvider(provider_config)

            with requests_mock.Mocker() as m:
                m.get(
                    "https://discord.com/api/v10/guilds/123456/emojis",
                    json=[
                        {"id": "123", "name": "valid", "animated": False},
                        {"id": "456", "name": None, "animated": False},  # Missing name
                        {"id": None, "name": "noId", "animated": False},  # Missing id
                    ],
                )

                emojis = provider.fetch_emojis()

                assert len(emojis) == 1
                assert "valid" in emojis

    def test_filter_emojis(
        self,
        discord_api_response: list,
    ) -> None:
        """Test emoji filtering."""
        config = ProviderConfig(
            type=ProviderType.DISCORD,
            namespace="discord",
            token_env="DISCORD_TOKEN",
            tenant_id="DISCORD_GUILD_ID",
        )
        config.filters.include_patterns = ["party*"]

        with patch.dict(os.environ, {"DISCORD_TOKEN": "test-token", "DISCORD_GUILD_ID": "123456"}):
            provider = DiscordEmojiProvider(config)

            with requests_mock.Mocker() as m:
                m.get(
                    "https://discord.com/api/v10/guilds/123456/emojis",
                    json=discord_api_response,
                )

                emojis = provider.fetch_emojis()

                assert "partyparrot" in emojis
                assert "catjam" not in emojis

    def test_get_required_env_vars(self, provider_config: ProviderConfig) -> None:
        """Test getting required environment variables."""
        with patch.dict(os.environ, {"DISCORD_TOKEN": "test-token", "DISCORD_GUILD_ID": "123456"}):
            provider = DiscordEmojiProvider(provider_config)
            env_vars = provider.get_required_env_vars()
            assert "DISCORD_TOKEN" in env_vars
            assert "DISCORD_GUILD_ID" in env_vars

    def test_validate_config_success(
        self,
        provider_config: ProviderConfig,
        discord_api_response: list,
    ) -> None:
        """Test successful config validation returns emoji count."""
        with patch.dict(os.environ, {"DISCORD_TOKEN": "test-token", "DISCORD_GUILD_ID": "123456"}):
            provider = DiscordEmojiProvider(provider_config)

            with requests_mock.Mocker() as m:
                m.get(
                    "https://discord.com/api/v10/guilds/123456/emojis",
                    json=discord_api_response,
                )

                emoji_count = provider.validate_config()
                assert emoji_count == 3

    def test_validate_config_invalid_token(self, provider_config: ProviderConfig) -> None:
        """Test validation fails with invalid token."""
        with patch.dict(os.environ, {"DISCORD_TOKEN": "test-token", "DISCORD_GUILD_ID": "123456"}):
            provider = DiscordEmojiProvider(provider_config)

            with requests_mock.Mocker() as m:
                m.get(
                    "https://discord.com/api/v10/guilds/123456/emojis",
                    status_code=401,
                )

                with pytest.raises(ProviderError, match="Invalid Discord token"):
                    provider.validate_config()

    def test_validate_config_missing_permission(self, provider_config: ProviderConfig) -> None:
        """Test validation fails when bot lacks permission."""
        with patch.dict(os.environ, {"DISCORD_TOKEN": "test-token", "DISCORD_GUILD_ID": "123456"}):
            provider = DiscordEmojiProvider(provider_config)

            with requests_mock.Mocker() as m:
                m.get(
                    "https://discord.com/api/v10/guilds/123456/emojis",
                    status_code=403,
                )

                with pytest.raises(ProviderError, match="lacks permission"):
                    provider.validate_config()

    def test_validate_config_guild_not_found(self, provider_config: ProviderConfig) -> None:
        """Test validation fails when guild not found."""
        with patch.dict(os.environ, {"DISCORD_TOKEN": "test-token", "DISCORD_GUILD_ID": "123456"}):
            provider = DiscordEmojiProvider(provider_config)

            with requests_mock.Mocker() as m:
                m.get(
                    "https://discord.com/api/v10/guilds/123456/emojis",
                    status_code=404,
                )

                with pytest.raises(ProviderError, match="Guild not found"):
                    provider.validate_config()
