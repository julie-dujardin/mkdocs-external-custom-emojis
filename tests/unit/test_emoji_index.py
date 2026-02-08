"""Tests for emoji index and generator."""

from pathlib import Path
from unittest.mock import MagicMock, patch
from xml.etree.ElementTree import Element

import pytest

from mkdocs_external_emojis.emoji_index import (
    _MD_CONFIG_ATTR,
    EmojiIndexConfig,
    create_custom_emoji_index,
    custom_emoji_generator,
)


class TestEmojiIndexConfig:
    """Tests for EmojiIndexConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = EmojiIndexConfig()
        assert config.namespace_prefix_required is False
        assert config.emoji_paths == {}


class TestCustomEmojiGenerator:
    """Tests for custom_emoji_generator function."""

    @pytest.fixture
    def md_with_config(self) -> MagicMock:
        """Create a mock Markdown instance with emoji config."""
        md = MagicMock()
        config = EmojiIndexConfig()
        setattr(md, _MD_CONFIG_ATTR, config)
        return md

    def test_generates_img_element_for_custom_emoji(self, md_with_config: MagicMock) -> None:
        """Test that custom emojis generate img elements."""
        # Register a custom emoji path
        config = getattr(md_with_config, _MD_CONFIG_ATTR)
        config.emoji_paths["partyparrot"] = "assets/emojis/slack/partyparrot.gif"

        element = custom_emoji_generator(
            index="partyparrot",
            shortname=":partyparrot:",
            alias=":partyparrot:",
            uc=None,
            alt="partyparrot",
            title=":partyparrot:",
            category="custom",
            options={},
            md=md_with_config,
        )

        assert isinstance(element, Element)
        assert element.tag == "img"
        assert element.get("class") == "twemoji"
        assert element.get("src") == "/assets/emojis/slack/partyparrot.gif"
        assert element.get("alt") == ":partyparrot:"
        assert element.get("title") == ":partyparrot:"

    def test_handles_namespaced_emoji(self, md_with_config: MagicMock) -> None:
        """Test that namespaced emojis work correctly."""
        config = getattr(md_with_config, _MD_CONFIG_ATTR)
        config.emoji_paths["slack-partyparrot"] = "assets/emojis/slack/partyparrot.gif"

        element = custom_emoji_generator(
            index="slack-partyparrot",
            shortname=":slack-partyparrot:",
            alias=":slack-partyparrot:",
            uc=None,
            alt="slack-partyparrot",
            title=":slack-partyparrot:",
            category="custom",
            options={},
            md=md_with_config,
        )

        assert element.tag == "img"
        assert element.get("src") == "/assets/emojis/slack/partyparrot.gif"

    def test_falls_back_to_standard_emoji(self) -> None:
        """Test that unknown emojis fall back to standard generator."""
        # md without config - should fall back to standard
        md = MagicMock()

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
                md=md,
            )

            mock_to_svg.assert_called_once()
            assert result == mock_element


class TestCreateCustomEmojiIndex:
    """Tests for create_custom_emoji_index function."""

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

    def test_stores_emoji_paths_on_md_instance(self, icons_dir: Path) -> None:
        """Test that emoji paths are stored on md instance."""
        md = MagicMock()

        with patch("mkdocs_external_emojis.emoji_index.twemoji") as mock_twemoji:
            mock_twemoji.return_value = {"emoji": {}, "alias": {}}

            create_custom_emoji_index(icons_dir, {}, md)

            # Config should be stored on md instance
            config = getattr(md, _MD_CONFIG_ATTR)
            assert "slack-partyparrot" in config.emoji_paths
            assert "partyparrot" in config.emoji_paths
            assert config.emoji_paths["slack-partyparrot"] == "assets/emojis/slack/partyparrot.gif"

    def test_namespace_prefix_required(self, icons_dir: Path) -> None:
        """Test that namespace prefix can be required."""
        with patch("mkdocs_external_emojis.emoji_index.twemoji") as mock_twemoji:
            mock_twemoji.return_value = {"emoji": {}, "alias": {}}

            index = create_custom_emoji_index(
                icons_dir, {}, MagicMock(), namespace_prefix_required=True
            )

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

    def test_config_stored_on_md_instance(self, icons_dir: Path) -> None:
        """Test that config is stored on md instance."""
        md = MagicMock()

        with patch("mkdocs_external_emojis.emoji_index.twemoji") as mock_twemoji:
            mock_twemoji.return_value = {"emoji": {}, "alias": {}}

            create_custom_emoji_index(icons_dir, {}, md)

            config = getattr(md, _MD_CONFIG_ATTR)
            assert isinstance(config, EmojiIndexConfig)
