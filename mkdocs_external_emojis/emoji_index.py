"""Custom emoji index for pymdownx.emoji integration."""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any
from xml.etree.ElementTree import Element

from material.extensions.emoji import to_svg, twemoji

from mkdocs_external_emojis.constants import LOGGER_NAME

if TYPE_CHECKING:
    from markdown import Markdown

logger = logging.getLogger(LOGGER_NAME)

# Attribute name for storing config on Markdown instance
_MD_CONFIG_ATTR = "_external_emoji_config"


@dataclass
class EmojiIndexConfig:
    """Configuration for the emoji index."""

    base_path: str = "/"
    namespace_prefix_required: bool = False
    emoji_paths: dict[str, str] = field(default_factory=dict)


def create_custom_emoji_index(
    icons_dir: Path,
    options: dict[str, Any],
    md: "Markdown",
    base_path: str = "/",
    namespace_prefix_required: bool = False,
) -> dict[str, Any]:
    """
    Create emoji index including both standard emojis and custom ones.

    Args:
        icons_dir: Path to custom icons directory
        options: Options from pymdownx.emoji
        md: Markdown instance
        base_path: Base path for emoji URLs
        namespace_prefix_required: Whether namespace prefix is required

    Returns:
        Emoji index dictionary
    """
    # Start with standard Twemoji index
    index = twemoji(options, md)

    # Create fresh config for this build and store on md instance
    config = EmojiIndexConfig(
        base_path=base_path,
        namespace_prefix_required=namespace_prefix_required,
    )
    setattr(md, _MD_CONFIG_ATTR, config)

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
                config.emoji_paths[full_name] = rel_path
                # Use a placeholder Unicode (U+E000 is in Private Use Area)
                index["emoji"][full_name_with_colons] = {
                    "name": full_name,
                    "unicode": "e000",  # Private Use Area placeholder
                    "category": "custom",
                }
                index["alias"][full_name_with_colons] = full_name_with_colons

                # Also add without prefix (e.g., :partyparrot:) unless namespace prefix is required
                if not namespace_prefix_required:
                    emoji_name_with_colons = f":{emoji_name}:"
                    config.emoji_paths[emoji_name] = rel_path
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
    options: dict[str, Any],
    md: "Markdown",
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
    # Get config from md instance
    config: EmojiIndexConfig | None = getattr(md, _MD_CONFIG_ATTR, None)

    # Clean up shortname to get emoji name
    emoji_name = shortname.strip(":")

    # Check if this is a custom emoji
    if config and emoji_name in config.emoji_paths:
        # Custom emoji - return img Element
        path = config.emoji_paths[emoji_name]

        # Create img element
        el = Element("img")
        el.set("class", "twemoji")
        el.set("alt", title)  # Use title (e.g., :partyparrot:) for accessibility
        el.set("title", title)
        el.set("src", f"{config.base_path}{path}")

        return el

    # Fall back to standard emoji generator
    return to_svg(index, shortname, alias, uc, alt, title, category, options, md)
