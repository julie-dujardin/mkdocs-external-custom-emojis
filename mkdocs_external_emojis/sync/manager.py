"""Sync manager for coordinating emoji downloads and caching."""

import shutil
from collections.abc import Callable
from pathlib import Path

from mkdocs_external_emojis.models import (
    CacheConfig,
    EmojiOptions,
    SyncResult,
)
from mkdocs_external_emojis.providers.base import AbstractEmojiProvider
from mkdocs_external_emojis.sync.cache import EmojiCache
from mkdocs_external_emojis.sync.downloader import DownloadError, EmojiDownloader


class SyncManager:
    """Manages emoji synchronization from providers to local storage."""

    def __init__(
        self,
        cache_config: CacheConfig,
        emoji_options: EmojiOptions,
        icons_dir: Path = Path("overrides/assets/emojis"),
    ) -> None:
        """
        Initialize sync manager.

        Args:
            cache_config: Cache configuration
            emoji_options: Global emoji options
            icons_dir: Directory where icons should be synced for MkDocs
        """
        self.cache_config = cache_config
        self.emoji_options = emoji_options
        self.icons_dir = icons_dir
        self.downloader = EmojiDownloader(
            max_size_kb=emoji_options.max_size_kb,
            timeout=30,
        )

    def sync_provider(
        self,
        provider: AbstractEmojiProvider,
        force: bool = False,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> SyncResult:
        """
        Sync emojis from a provider.

        Args:
            provider: Emoji provider
            force: Force re-download even if cached
            progress_callback: Optional callback(emoji_name, current, total)

        Returns:
            Sync result with statistics
        """
        namespace = provider.config.namespace
        cache = EmojiCache(self.cache_config, namespace)

        # Fetch emoji list from provider
        try:
            emojis = provider.fetch_emojis()
        except Exception as e:
            return SyncResult(
                provider=provider.config.type.value,
                namespace=namespace,
                total_emojis=0,
                synced=0,
                cached=0,
                skipped=0,
                errors=[f"Failed to fetch emojis: {e}"],
            )

        result = SyncResult(
            provider=provider.config.type.value,
            namespace=namespace,
            total_emojis=len(emojis),
            synced=0,
            cached=0,
            skipped=0,
        )

        # Clean cache if requested
        if self.cache_config.clean_on_build or force:
            cache.clean()

        # Download emojis
        for i, (name, emoji) in enumerate(emojis.items(), 1):
            if progress_callback:
                progress_callback(name, i, len(emojis))

            # Skip if cached and not forcing
            if not force and cache.is_cached(emoji):
                result.cached += 1
                continue

            # Skip if no URL (shouldn't happen after alias resolution)
            if not emoji.url:
                result.skipped += 1
                result.errors.append(f"No URL for emoji: {name}")
                continue

            # Download emoji
            try:
                temp_path, size = self.downloader.download(emoji)

                # Store in cache
                cache.store(emoji, temp_path, size)

                # Clean up temp file
                temp_path.unlink()

                result.synced += 1

            except DownloadError as e:
                result.errors.append(str(e))
                result.skipped += 1

        # Sync cached emojis to icons directory
        self._sync_to_icons(cache, namespace)

        return result

    def _sync_to_icons(self, cache: EmojiCache, namespace: str) -> None:
        """
        Sync cached emojis to MkDocs icons directory.

        Args:
            cache: Emoji cache
            namespace: Provider namespace
        """
        # Create namespace directory in icons dir
        namespace_dir = self.icons_dir / namespace
        namespace_dir.mkdir(parents=True, exist_ok=True)

        # Copy all cached emojis
        for file in cache.cache_dir.iterdir():
            if file.name == cache.METADATA_FILE:
                continue

            dest = namespace_dir / file.name
            shutil.copy2(file, dest)

    def clean_namespace(self, namespace: str) -> None:
        """
        Clean all emojis for a namespace.

        Args:
            namespace: Provider namespace
        """
        # Clean cache
        cache = EmojiCache(self.cache_config, namespace)
        cache.clean()

        # Clean icons directory
        namespace_dir = self.icons_dir / namespace
        if namespace_dir.exists():
            shutil.rmtree(namespace_dir)
