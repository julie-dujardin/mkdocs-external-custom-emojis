"""MkDocs plugin for external custom emojis."""

import contextlib
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from mkdocs.config import base, config_options
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import File, Files
from mkdocs.structure.pages import _AbsoluteLinksValidationValue

from mkdocs_external_emojis.config import ConfigError, load_config, validate_environment
from mkdocs_external_emojis.constants import DEFAULT_CONFIG_FILE, LOGGER_NAME
from mkdocs_external_emojis.emoji_index import (
    create_custom_emoji_index,
    custom_emoji_generator,
)
from mkdocs_external_emojis.providers import ProviderError, create_provider
from mkdocs_external_emojis.sync import SyncManager

if TYPE_CHECKING:
    from mkdocs_external_emojis.models import EmojiConfig

logger = logging.getLogger(LOGGER_NAME)


class ExternalEmojisPluginConfig(base.Config):
    """Plugin configuration schema."""

    config_file = config_options.Type(str, default=DEFAULT_CONFIG_FILE)
    icons_dir = config_options.Type(str, default="overrides/assets/emojis")
    enabled = config_options.Type(bool, default=True)
    fail_on_error = config_options.Type(bool, default=True)


class ExternalEmojisPlugin(BasePlugin[ExternalEmojisPluginConfig]):
    """MkDocs plugin to sync custom emojis from external providers."""

    def __init__(self) -> None:
        """Initialize plugin."""
        super().__init__()
        self.emoji_config: EmojiConfig | None = None
        self.sync_manager: SyncManager | None = None

    def on_config(self, config: Any) -> Any:
        """
        Load emoji configuration and prepare for sync.

        Args:
            config: MkDocs configuration

        Returns:
            Updated MkDocs configuration
        """
        if not self.config.enabled:
            logger.info("External emojis plugin is disabled")
            return config

        # Load emoji configuration
        try:
            self.emoji_config = load_config(self.config.config_file)
        except ConfigError as e:
            error_msg = f"Failed to load emoji configuration: {e}"
            if self.config.fail_on_error:
                raise ConfigError(error_msg) from e
            logger.warning(error_msg)
            return config

        # Initialize icons directory
        icons_dir = Path(self.config.icons_dir)

        # Tell MkDocs to resolve absolute links (like /assets/emojis/...) against
        # the files collection instead of warning about them. This works because
        # on_files registers all emoji files so MkDocs can find and resolve them.
        with contextlib.suppress(KeyError, TypeError):
            config["validation"]["links"]["absolute_links"] = (
                _AbsoluteLinksValidationValue.RELATIVE_TO_DOCS
            )

        # Configure pymdownx.emoji first (works with cached emojis even if sync fails)
        self._configure_pymdownx_emoji(config, icons_dir)

        # Validate environment variables
        missing_vars = validate_environment(self.emoji_config)
        if missing_vars:
            error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
            if self.config.fail_on_error:
                raise ConfigError(error_msg)
            logger.warning(error_msg)
            # Skip sync manager initialization but emoji rendering still works
            return config

        # Initialize sync manager
        self.sync_manager = SyncManager(
            cache_config=self.emoji_config.cache,
            emoji_options=self.emoji_config.emojis,
            icons_dir=icons_dir,
        )

        logger.info(
            f"External emojis plugin initialized with "
            f"{len(self.emoji_config.get_enabled_providers())} provider(s)"
        )

        return config

    def on_pre_build(self, config: Any) -> None:
        """
        Sync emojis before building documentation.

        Args:
            config: MkDocs configuration
        """
        if not self.config.enabled or not self.emoji_config or not self.sync_manager:
            return

        logger.info("Syncing emojis from external providers...")

        # Sync each enabled provider
        for provider_config in self.emoji_config.get_enabled_providers():
            logger.info(
                f"Syncing {provider_config.type.value} "
                f"provider (namespace: {provider_config.namespace})..."
            )

            # Create provider instance
            try:
                provider = create_provider(provider_config)
            except ProviderError as e:
                error_msg = f"Failed to initialize provider {provider_config.namespace}: {e}"
                if self.config.fail_on_error:
                    raise ProviderError(error_msg) from e
                logger.warning(error_msg)
                continue

            # Sync emojis
            try:
                result = self.sync_manager.sync_provider(provider)

                logger.info(
                    f"Synced {result.synced} emojis, {result.cached} cached, "
                    f"{result.skipped} skipped for {provider_config.namespace}"
                )

                if result.errors:
                    logger.warning(
                        f"Encountered {len(result.errors)} errors while syncing "
                        f"{provider_config.namespace}"
                    )
                    for error in result.errors[:5]:  # Show first 5 errors
                        logger.warning(f"  - {error}")
                    if len(result.errors) > 5:
                        logger.warning(f"  ... and {len(result.errors) - 5} more")

            except Exception as e:
                error_msg = f"Failed to sync {provider_config.namespace}: {e}"
                if self.config.fail_on_error:
                    raise ProviderError(error_msg) from e
                logger.warning(error_msg)

        logger.info("Emoji sync complete")

    def on_files(self, files: Files, config: Any) -> Files:
        """Register emoji files with MkDocs so it handles copying and path resolution."""
        if not self.config.enabled:
            return files

        icons_dir = Path(self.config.icons_dir)
        if not icons_dir.exists():
            return files

        site_dir = config["site_dir"]
        use_directory_urls = config.get("use_directory_urls", True)

        for emoji_file in icons_dir.rglob("*"):
            if emoji_file.is_file() and not emoji_file.name.startswith("."):
                rel_path = str(emoji_file.relative_to(icons_dir))
                src_path = f"assets/emojis/{rel_path}"
                files.append(
                    File(
                        src_path,
                        src_dir=str(icons_dir.parent.parent),
                        dest_dir=site_dir,
                        use_directory_urls=use_directory_urls,
                    )
                )

        return files

    def _configure_pymdownx_emoji(self, config: Any, icons_dir: Path) -> None:
        """
        Configure pymdownx.emoji with custom emoji index and generator.

        Args:
            config: MkDocs configuration
            icons_dir: Path to icons directory
        """
        if "markdown_extensions" not in config:
            logger.warning(
                "markdown_extensions not found in mkdocs.yml - emojis may not render correctly"
            )
            return

        # Check if pymdownx.emoji is in markdown_extensions
        md_extensions = config["markdown_extensions"]
        emoji_extension_found = False

        for ext in md_extensions:
            # Check both string and dict formats
            ext_name = (
                ext
                if isinstance(ext, str)
                else next(iter(ext.keys()))
                if isinstance(ext, dict)
                else None
            )
            if ext_name == "pymdownx.emoji":
                emoji_extension_found = True
                break

        if not emoji_extension_found:
            logger.warning(
                "pymdownx.emoji extension not found in markdown_extensions - "
                "emojis will not be available. Please add it to your mkdocs.yml"
            )
            return

        # Get namespace prefix requirement from emoji config
        namespace_prefix_required = (
            self.emoji_config.emojis.namespace_prefix_required if self.emoji_config else False
        )

        # Configure pymdownx.emoji with our custom emoji index and generator
        if "mdx_configs" not in config:
            config["mdx_configs"] = {}

        if "pymdownx.emoji" not in config["mdx_configs"]:
            config["mdx_configs"]["pymdownx.emoji"] = {}

        emoji_config = config["mdx_configs"]["pymdownx.emoji"]

        # Set custom emoji index function (accepts options and md from pymdownx.emoji)
        def emoji_index_wrapper(options: dict[str, Any], md: Any) -> dict[str, Any]:
            return create_custom_emoji_index(
                icons_dir, options, md, namespace_prefix_required=namespace_prefix_required
            )

        emoji_config["emoji_index"] = emoji_index_wrapper

        # Set custom emoji generator
        emoji_config["emoji_generator"] = custom_emoji_generator

        logger.info(f"Configured custom emoji system with icons from: {icons_dir}")
