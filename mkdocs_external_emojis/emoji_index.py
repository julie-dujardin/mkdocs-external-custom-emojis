"""Custom emoji index for pymdownx.emoji integration."""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import Element

from material.extensions.emoji import to_svg, twemoji

logger = logging.getLogger("mkdocs.plugins.external-emojis")


@dataclass
class EmojiIndexConfig:
    """Configuration for the emoji index."""

    base_path: str = "/"
    namespace_prefix_required: bool = False
    emoji_paths: dict[str, str] = field(default_factory=dict)

    def reset(self) -> None:
        """Reset emoji paths for a fresh build."""
        self.emoji_paths.clear()


# Module-level singleton instance
emoji_index_config = EmojiIndexConfig()


def create_custom_emoji_index(icons_dir: Path, options: dict[str, Any], md: Any) -> dict[str, Any]:
    """
    Create emoji index including both standard emojis and custom ones.

    Args:
        icons_dir: Path to custom icons directory
        options: Options from pymdownx.emoji
        md: Markdown instance

    Returns:
        Emoji index dictionary
    """
    # Start with standard Twemoji index
    index = twemoji(options, md)

    # Add custom emojis from each namespace
    emoji_index_config.reset()

    if icons_dir.exists():
        for namespace_dir in icons_dir.iterdir():
            if not namespace_dir.is_dir():
                continue

            namespace = namespace_dir.name

            # Scan for emoji files
            for emoji_file in namespace_dir.iterdir():
                if emoji_file.name.startswith("."):
                    continue

                # Get emoji name without extension
                emoji_name = emoji_file.stem

                # Store relative path for the generator to use
                rel_path = f"assets/emojis/{namespace}/{emoji_file.name}"

                # Add to the emoji index with both prefixed and unprefixed names
                if "emoji" not in index:
                    index["emoji"] = {}
                if "alias" not in index:
                    index["alias"] = {}

                # Add with namespace prefix (e.g., :slack-partyparrot:)
                full_name = f"{namespace}-{emoji_name}"
                full_name_with_colons = f":{full_name}:"
                emoji_index_config.emoji_paths[full_name] = rel_path
                # Use a placeholder Unicode (U+E000 is in Private Use Area)
                index["emoji"][full_name_with_colons] = {
                    "name": full_name,
                    "unicode": "e000",  # Private Use Area placeholder
                    "category": "custom",
                }
                index["alias"][full_name_with_colons] = full_name_with_colons

                # Also add without prefix (e.g., :partyparrot:) unless namespace prefix is required
                if not emoji_index_config.namespace_prefix_required:
                    emoji_name_with_colons = f":{emoji_name}:"
                    emoji_index_config.emoji_paths[emoji_name] = rel_path
                    index["emoji"][emoji_name_with_colons] = {
                        "name": emoji_name,
                        "unicode": "e000",  # Private Use Area placeholder
                        "category": "custom",
                    }
                    index["alias"][emoji_name_with_colons] = emoji_name_with_colons

    return index


def custom_emoji_generator(
    index: str,
    shortname: str,
    alias: str,
    uc: str | None,
    alt: str,
    title: str,
    category: str,
    options: Any,
    md: Any,
) -> Element:
    """
    Custom emoji generator that handles both standard and custom emojis.

    Args:
        index: Emoji code/identifier (string)
        shortname: Emoji shortname (e.g., :partyparrot:)
        alias: Alias name
        uc: Unicode codepoint or None
        alt: Alt text
        title: Title text
        category: Category
        options: Generator options
        md: Markdown instance

    Returns:
        HTML for the emoji
    """
    # Clean up shortname to get emoji name
    emoji_name = shortname.strip(":")

    # Check if this is a custom emoji
    if emoji_name in emoji_index_config.emoji_paths:
        # Custom emoji - return img Element
        path = emoji_index_config.emoji_paths[emoji_name]

        # Create img element
        el = Element("img")
        el.set("class", "twemoji")
        el.set("alt", alt)
        el.set("title", title)
        el.set("src", f"{emoji_index_config.base_path}{path}")

        return el

    # Fall back to standard emoji generator
    return to_svg(index, shortname, alias, uc, alt, title, category, options, md)
