"""Tests for Slack emoji provider."""

import os
from unittest.mock import patch

import pytest
import requests
import requests_mock

from mkdocs_external_emojis.models import ProviderConfig, ProviderType
from mkdocs_external_emojis.providers import ProviderError, SlackEmojiProvider


class TestSlackEmojiProvider:
    """Tests for SlackEmojiProvider."""

    @pytest.fixture
    def provider_config(self) -> ProviderConfig:
        """Create test provider configuration."""
        return ProviderConfig(
            type=ProviderType.SLACK,
            namespace="slack",
            token_env="SLACK_TOKEN",
        )

    @pytest.fixture
    def slack_api_response(self) -> dict:
        """Mock Slack API response."""
        return {
            "ok": True,
            "emoji": {
                "partyparrot": "https://example.com/partyparrot.gif",
                "catjam": "https://example.com/catjam.gif",
                "oldcat": "alias:catjam",
            },
        }

    def test_initialization_without_token(self, provider_config: ProviderConfig) -> None:
        """Test that initialization fails without token."""
        with pytest.raises(ProviderError, match="not found in environment"):
            SlackEmojiProvider(provider_config)

    def test_initialization_with_token(self, provider_config: ProviderConfig) -> None:
        """Test successful initialization with token."""
        with patch.dict(os.environ, {"SLACK_TOKEN": "xoxp-test-token"}):
            provider = SlackEmojiProvider(provider_config)
            assert provider.token == "xoxp-test-token"

    def test_fetch_emojis_success(
        self,
        provider_config: ProviderConfig,
        slack_api_response: dict,
    ) -> None:
        """Test successful emoji fetching."""
        with patch.dict(os.environ, {"SLACK_TOKEN": "xoxp-test-token"}):
            provider = SlackEmojiProvider(provider_config)

            with requests_mock.Mocker() as m:
                m.get(
                    "https://slack.com/api/emoji.list",
                    json=slack_api_response,
                )

                emojis = provider.fetch_emojis()

                # Should have 3 emojis (2 regular + 1 alias resolved)
                assert len(emojis) == 3
                assert "partyparrot" in emojis
                assert "catjam" in emojis
                assert "oldcat" in emojis

                # Check regular emoji
                assert emojis["partyparrot"].url == "https://example.com/partyparrot.gif"

                # Check alias was resolved
                assert emojis["oldcat"].url == "https://example.com/catjam.gif"

    def test_fetch_emojis_api_error(
        self,
        provider_config: ProviderConfig,
    ) -> None:
        """Test handling of API errors."""
        with patch.dict(os.environ, {"SLACK_TOKEN": "xoxp-test-token"}):
            provider = SlackEmojiProvider(provider_config)

            with requests_mock.Mocker() as m:
                m.get(
                    "https://slack.com/api/emoji.list",
                    json={"ok": False, "error": "invalid_auth"},
                )

                with pytest.raises(ProviderError, match="invalid_auth"):
                    provider.fetch_emojis()

    def test_fetch_emojis_network_error(
        self,
        provider_config: ProviderConfig,
    ) -> None:
        """Test handling of network errors."""
        with patch.dict(os.environ, {"SLACK_TOKEN": "xoxp-test-token"}):
            provider = SlackEmojiProvider(provider_config)

            with requests_mock.Mocker() as m:
                m.get(
                    "https://slack.com/api/emoji.list",
                    exc=requests.exceptions.ConnectTimeout,
                )

                with pytest.raises(ProviderError, match="Failed to fetch"):
                    provider.fetch_emojis()

    def test_filter_emojis(
        self,
        slack_api_response: dict,
    ) -> None:
        """Test emoji filtering."""
        config = ProviderConfig(
            type=ProviderType.SLACK,
            namespace="slack",
            token_env="SLACK_TOKEN",
        )
        config.filters.include_patterns = ["party*"]

        with patch.dict(os.environ, {"SLACK_TOKEN": "xoxp-test-token"}):
            provider = SlackEmojiProvider(config)

            with requests_mock.Mocker() as m:
                m.get(
                    "https://slack.com/api/emoji.list",
                    json=slack_api_response,
                )

                emojis = provider.fetch_emojis()

                # Should only include partyparrot
                assert "partyparrot" in emojis
                assert "catjam" not in emojis

    def test_get_required_env_vars(self, provider_config: ProviderConfig) -> None:
        """Test getting required environment variables."""
        with patch.dict(os.environ, {"SLACK_TOKEN": "xoxp-test-token"}):
            provider = SlackEmojiProvider(provider_config)
            assert provider.get_required_env_vars() == ["SLACK_TOKEN"]

    def test_validate_config_success(
        self,
        provider_config: ProviderConfig,
        slack_api_response: dict,
    ) -> None:
        """Test successful config validation returns emoji count."""
        with patch.dict(os.environ, {"SLACK_TOKEN": "xoxp-test-token"}):
            provider = SlackEmojiProvider(provider_config)

            with requests_mock.Mocker() as m:
                m.get(
                    "https://slack.com/api/auth.test",
                    json={"ok": True, "user": "test_user"},
                )
                m.get(
                    "https://slack.com/api/emoji.list",
                    json=slack_api_response,
                )

                emoji_count = provider.validate_config()
                assert emoji_count == 3

    def test_validate_config_invalid_token(
        self,
        provider_config: ProviderConfig,
    ) -> None:
        """Test validation fails with invalid token."""
        with patch.dict(os.environ, {"SLACK_TOKEN": "xoxp-test-token"}):
            provider = SlackEmojiProvider(provider_config)

            with requests_mock.Mocker() as m:
                m.get(
                    "https://slack.com/api/auth.test",
                    json={"ok": False, "error": "invalid_auth"},
                )

                with pytest.raises(ProviderError, match="Invalid Slack token"):
                    provider.validate_config()

    def test_validate_config_missing_emoji_permission(
        self,
        provider_config: ProviderConfig,
    ) -> None:
        """Test validation fails when token lacks emoji:read permission."""
        with patch.dict(os.environ, {"SLACK_TOKEN": "xoxp-test-token"}):
            provider = SlackEmojiProvider(provider_config)

            with requests_mock.Mocker() as m:
                m.get(
                    "https://slack.com/api/auth.test",
                    json={"ok": True, "user": "test_user"},
                )
                m.get(
                    "https://slack.com/api/emoji.list",
                    json={"ok": False, "error": "missing_scope"},
                )

                with pytest.raises(ProviderError, match="emoji:read permission"):
                    provider.validate_config()
