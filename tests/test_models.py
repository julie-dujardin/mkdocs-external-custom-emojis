"""Tests for data models."""

from mkdocs_external_emojis.models import (
    EmojiFormat,
    EmojiInfo,
    EmojiOptions,
    ProviderConfig,
    ProviderType,
)


class TestEmojiInfo:
    """Tests for EmojiInfo model."""

    def test_from_url(self) -> None:
        """Test creating EmojiInfo from URL."""
        emoji = EmojiInfo.from_url("test", "https://example.com/emoji.png")

        assert emoji.name == "test"
        assert emoji.url == "https://example.com/emoji.png"
        assert emoji.format == EmojiFormat.PNG
        assert not emoji.is_alias

    def test_from_url_detects_format(self) -> None:
        """Test format detection from URL."""
        test_cases = [
            ("https://example.com/emoji.svg", EmojiFormat.SVG),
            ("https://example.com/emoji.png", EmojiFormat.PNG),
            ("https://example.com/emoji.gif", EmojiFormat.GIF),
            ("https://example.com/emoji.jpg", EmojiFormat.JPG),
        ]

        for url, expected_format in test_cases:
            emoji = EmojiInfo.from_url("test", url)
            assert emoji.format == expected_format

    def test_from_alias(self) -> None:
        """Test creating EmojiInfo for alias."""
        emoji = EmojiInfo.from_alias("myalias", "target")

        assert emoji.name == "myalias"
        assert emoji.url is None
        assert emoji.alias_of == "target"
        assert emoji.is_alias

    def test_is_alias(self) -> None:
        """Test is_alias property."""
        regular = EmojiInfo.from_url("regular", "https://example.com/test.png")
        alias = EmojiInfo.from_alias("alias", "regular")

        assert not regular.is_alias
        assert alias.is_alias


class TestProviderConfig:
    """Tests for ProviderConfig model."""

    def test_initialization(self) -> None:
        """Test basic initialization."""
        config = ProviderConfig(
            type=ProviderType.SLACK,
            namespace="slack",
            token_env="SLACK_TOKEN",
        )

        assert config.type == ProviderType.SLACK
        assert config.namespace == "slack"
        assert config.token_env == "SLACK_TOKEN"
        assert config.enabled is True

    def test_type_conversion(self) -> None:
        """Test string to ProviderType conversion."""
        config = ProviderConfig(
            type="slack",  # type: ignore
            namespace="slack",
            token_env="SLACK_TOKEN",
        )

        assert config.type == ProviderType.SLACK


class TestEmojiOptions:
    """Tests for EmojiOptions model."""

    def test_format_emoji_name_namespace_dash(self) -> None:
        """Test namespace-name format."""
        options = EmojiOptions(prefix_format="namespace-name")
        result = options.format_emoji_name("slack", "partyparrot")
        assert result == "slack-partyparrot"

    def test_format_emoji_name_namespace_underscore(self) -> None:
        """Test namespace_name format."""
        options = EmojiOptions(prefix_format="namespace_name")
        result = options.format_emoji_name("slack", "partyparrot")
        assert result == "slack_partyparrot"

    def test_format_emoji_name_only(self) -> None:
        """Test name-only format."""
        options = EmojiOptions(prefix_format="name-only")
        result = options.format_emoji_name("slack", "partyparrot")
        assert result == "partyparrot"

    def test_format_emoji_name_invalid_fallback(self) -> None:
        """Test invalid format falls back to namespace-name."""
        options = EmojiOptions(prefix_format="invalid-format")
        result = options.format_emoji_name("slack", "partyparrot")
        assert result == "slack-partyparrot"

    def test_format_emoji_name_default(self) -> None:
        """Test default format is namespace-name."""
        options = EmojiOptions()
        result = options.format_emoji_name("slack", "partyparrot")
        assert result == "slack-partyparrot"
