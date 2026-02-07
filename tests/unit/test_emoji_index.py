"""Tests for emoji index and generator."""

from pathlib import Path
from unittest.mock import MagicMock, patch
from xml.etree.ElementTree import Element

import pytest

from mkdocs_external_emojis.emoji_index import (
    EmojiIndexConfig,
    create_custom_emoji_index,
    custom_emoji_generator,
    emoji_index_config,
)


class TestEmojiIndexConfig:
    """Tests for EmojiIndexConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = EmojiIndexConfig()
        assert config.base_path == "/"
        assert config.namespace_prefix_required is False
        assert config.emoji_paths == {}

    def test_reset_clears_emoji_paths(self) -> None:
        """Test that reset clears emoji paths."""
        config = EmojiIndexConfig()
        config.emoji_paths["test"] = "/path/to/test.png"
        config.emoji_paths["other"] = "/path/to/other.gif"

        config.reset()

        assert config.emoji_paths == {}


class TestCustomEmojiGenerator:
    """Tests for custom_emoji_generator function."""

    @pytest.fixture(autouse=True)
    def reset_config(self) -> None:
        """Reset emoji index config before each test."""
        emoji_index_config.reset()
        emoji_index_config.base_path = "/"

    def test_generates_img_element_for_custom_emoji(self) -> None:
        """Test that custom emojis generate img elements."""
        # Register a custom emoji path
        emoji_index_config.emoji_paths["partyparrot"] = "assets/emojis/slack/partyparrot.gif"

        element = custom_emoji_generator(
            index="partyparrot",
            shortname=":partyparrot:",
            alias=":partyparrot:",
            uc=None,
            alt="partyparrot",
            title=":partyparrot:",
            category="custom",
            options={},
            md=MagicMock(),
        )

        assert isinstance(element, Element)
        assert element.tag == "img"
        assert element.get("class") == "twemoji"
        assert element.get("src") == "/assets/emojis/slack/partyparrot.gif"
        assert element.get("alt") == ":partyparrot:"
        assert element.get("title") == ":partyparrot:"

    def test_respects_base_path(self) -> None:
        """Test that base_path is included in src URL."""
        emoji_index_config.emoji_paths["cat"] = "assets/emojis/test/cat.png"
        emoji_index_config.base_path = "/docs/"

        element = custom_emoji_generator(
            index="cat",
            shortname=":cat:",
            alias=":cat:",
            uc=None,
            alt="cat",
            title=":cat:",
            category="custom",
            options={},
            md=MagicMock(),
        )

        assert element.get("src") == "/docs/assets/emojis/test/cat.png"

    def test_handles_namespaced_emoji(self) -> None:
        """Test that namespaced emojis work correctly."""
        emoji_index_config.emoji_paths["slack-partyparrot"] = "assets/emojis/slack/partyparrot.gif"

        element = custom_emoji_generator(
            index="slack-partyparrot",
            shortname=":slack-partyparrot:",
            alias=":slack-partyparrot:",
            uc=None,
            alt="slack-partyparrot",
            title=":slack-partyparrot:",
            category="custom",
            options={},
            md=MagicMock(),
        )

        assert element.tag == "img"
        assert element.get("src") == "/assets/emojis/slack/partyparrot.gif"

    def test_falls_back_to_standard_emoji(self) -> None:
        """Test that unknown emojis fall back to standard generator."""
        # Don't register any custom emojis

        with patch("mkdocs_external_emojis.emoji_index.to_svg") as mock_to_svg:
            mock_element = Element("span")
            mock_to_svg.return_value = mock_element

            result = custom_emoji_generator(
                index="smile",
                shortname=":smile:",
                alias=":smile:",
                uc="1f604",
                alt="smile",
                title=":smile:",
                category="people",
                options={"opt": "value"},
                md=MagicMock(),
            )

            mock_to_svg.assert_called_once()
            assert result == mock_element


class TestCreateCustomEmojiIndex:
    """Tests for create_custom_emoji_index function."""

    @pytest.fixture(autouse=True)
    def reset_config(self) -> None:
        """Reset emoji index config before each test."""
        emoji_index_config.reset()

    @pytest.fixture
    def icons_dir(self, tmp_path: Path) -> Path:
        """Create a temporary icons directory with test emojis."""
        icons = tmp_path / "icons"
        icons.mkdir()

        # Create namespace directory
        slack_dir = icons / "slack"
        slack_dir.mkdir()

        # Create some emoji files
        (slack_dir / "partyparrot.gif").write_bytes(b"GIF89a")
        (slack_dir / "catjam.gif").write_bytes(b"GIF89a")
        (slack_dir / ".hidden").write_bytes(b"hidden")  # Should be ignored

        return icons

    def test_adds_custom_emojis_to_index(self, icons_dir: Path) -> None:
        """Test that custom emojis are added to the index."""
        with patch("mkdocs_external_emojis.emoji_index.twemoji") as mock_twemoji:
            mock_twemoji.return_value = {"emoji": {}, "alias": {}}

            index = create_custom_emoji_index(icons_dir, {}, MagicMock())

            # Should have both prefixed and unprefixed versions
            assert ":slack-partyparrot:" in index["emoji"]
            assert ":partyparrot:" in index["emoji"]
            assert ":slack-catjam:" in index["emoji"]
            assert ":catjam:" in index["emoji"]

    def test_skips_hidden_files(self, icons_dir: Path) -> None:
        """Test that hidden files are skipped."""
        with patch("mkdocs_external_emojis.emoji_index.twemoji") as mock_twemoji:
            mock_twemoji.return_value = {"emoji": {}, "alias": {}}

            index = create_custom_emoji_index(icons_dir, {}, MagicMock())

            assert ":hidden:" not in index["emoji"]
            assert ":.hidden:" not in index["emoji"]

    def test_stores_emoji_paths(self, icons_dir: Path) -> None:
        """Test that emoji paths are stored in config."""
        with patch("mkdocs_external_emojis.emoji_index.twemoji") as mock_twemoji:
            mock_twemoji.return_value = {"emoji": {}, "alias": {}}

            create_custom_emoji_index(icons_dir, {}, MagicMock())

            assert "slack-partyparrot" in emoji_index_config.emoji_paths
            assert "partyparrot" in emoji_index_config.emoji_paths
            assert (
                emoji_index_config.emoji_paths["slack-partyparrot"]
                == "assets/emojis/slack/partyparrot.gif"
            )

    def test_namespace_prefix_required(self, icons_dir: Path) -> None:
        """Test that namespace prefix can be required."""
        emoji_index_config.namespace_prefix_required = True

        with patch("mkdocs_external_emojis.emoji_index.twemoji") as mock_twemoji:
            mock_twemoji.return_value = {"emoji": {}, "alias": {}}

            index = create_custom_emoji_index(icons_dir, {}, MagicMock())

            # Should only have prefixed versions
            assert ":slack-partyparrot:" in index["emoji"]
            assert ":partyparrot:" not in index["emoji"]

    def test_handles_nonexistent_directory(self, tmp_path: Path) -> None:
        """Test that nonexistent directory is handled gracefully."""
        nonexistent = tmp_path / "nonexistent"

        with patch("mkdocs_external_emojis.emoji_index.twemoji") as mock_twemoji:
            mock_twemoji.return_value = {"emoji": {}, "alias": {}}

            index = create_custom_emoji_index(nonexistent, {}, MagicMock())

            # Should return base index without errors
            assert index == {"emoji": {}, "alias": {}}

    def test_handles_multiple_namespaces(self, tmp_path: Path) -> None:
        """Test that multiple namespaces are handled."""
        icons = tmp_path / "icons"
        icons.mkdir()

        # Create two namespace directories
        slack_dir = icons / "slack"
        slack_dir.mkdir()
        (slack_dir / "emoji1.png").write_bytes(b"PNG")

        discord_dir = icons / "discord"
        discord_dir.mkdir()
        (discord_dir / "emoji2.gif").write_bytes(b"GIF89a")

        with patch("mkdocs_external_emojis.emoji_index.twemoji") as mock_twemoji:
            mock_twemoji.return_value = {"emoji": {}, "alias": {}}

            index = create_custom_emoji_index(icons, {}, MagicMock())

            assert ":slack-emoji1:" in index["emoji"]
            assert ":discord-emoji2:" in index["emoji"]
