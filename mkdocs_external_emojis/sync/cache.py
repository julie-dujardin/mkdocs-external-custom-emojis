"""Cache management for downloaded emojis."""

import json
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, cast

from mkdocs_external_emojis.constants import LOGGER_NAME
from mkdocs_external_emojis.models import CacheConfig, EmojiInfo

logger = logging.getLogger(LOGGER_NAME)


class EmojiCache:
    """Manages caching of downloaded emoji files."""

    METADATA_FILE = ".metadata.json"

    def __init__(self, config: CacheConfig, namespace: str) -> None:
        """
        Initialize emoji cache.

        Args:
            config: Cache configuration
            namespace: Provider namespace
        """
        self.config = config
        self.namespace = namespace
        self.cache_dir = config.directory / namespace
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.metadata_file = self.cache_dir / self.METADATA_FILE
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> dict[str, Any]:
        """Load cache metadata from disk."""
        if not self.metadata_file.exists():
            return {}

        try:
            with open(self.metadata_file) as f:
                return cast("dict[str, Any]", json.load(f))
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(
                "Corrupt or unreadable cache metadata for %s, starting fresh: %s",
                self.namespace,
                e,
            )
            return {}

    def _save_metadata(self) -> None:
        """Save cache metadata to disk."""
        with open(self.metadata_file, "w") as f:
            json.dump(self.metadata, f, indent=2)

    def is_cached(self, emoji: EmojiInfo) -> bool:
        """
        Check if an emoji is cached and fresh.

        Args:
            emoji: Emoji to check

        Returns:
            True if emoji is cached and not stale
        """
        if emoji.name not in self.metadata:
            return False

        # Check if file exists
        cached_path = self._get_cached_path(emoji)
        if not cached_path.exists():
            return False

        # Check TTL
        cached_time = self.metadata[emoji.name].get("cached_at")
        if not cached_time:
            return False

        cached_dt = datetime.fromisoformat(cached_time)
        ttl = timedelta(hours=self.config.ttl_hours)

        return datetime.now() - cached_dt < ttl

    def get_cached_path(self, emoji: EmojiInfo) -> Path | None:
        """
        Get path to cached emoji file.

        Args:
            emoji: Emoji to get

        Returns:
            Path to cached file if exists, None otherwise
        """
        if not self.is_cached(emoji):
            return None

        path = self._get_cached_path(emoji)
        return path if path.exists() else None

    def _get_cached_path(self, emoji: EmojiInfo) -> Path:
        """Get expected path for cached emoji file."""
        # Get file extension from format or URL
        if emoji.format:
            ext = emoji.format.value
        elif emoji.url:
            # Try to extract from URL
            url_lower = emoji.url.lower()
            for possible_ext in ["svg", "png", "gif", "jpg", "webp"]:
                if f".{possible_ext}" in url_lower:
                    ext = possible_ext
                    break
            else:
                ext = "png"  # Default
        else:
            ext = "png"

        return self.cache_dir / f"{emoji.name}.{ext}"

    def store(
        self,
        emoji: EmojiInfo,
        file_path: Path,
        size_bytes: int,
    ) -> None:
        """
        Store emoji file in cache.

        Args:
            emoji: Emoji information
            file_path: Path to downloaded file
            size_bytes: Size of the file in bytes
        """
        cached_path = self._get_cached_path(emoji)

        # Copy file to cache
        shutil.copy2(file_path, cached_path)

        # Update metadata
        self.metadata[emoji.name] = {
            "url": emoji.url,
            "format": emoji.format.value if emoji.format else None,
            "size_bytes": size_bytes,
            "cached_at": datetime.now().isoformat(),
        }

        self._save_metadata()

    def clean(self) -> int:
        """
        Remove all cached emojis for this namespace.

        Returns:
            Number of files removed
        """
        count = 0
        if self.cache_dir.exists():
            for file in self.cache_dir.iterdir():
                if file.name != self.METADATA_FILE:
                    file.unlink()
                    count += 1

            # Clear metadata
            self.metadata = {}
            self._save_metadata()

        return count

    def clean_stale(self) -> int:
        """
        Remove stale cached emojis.

        Returns:
            Number of files removed
        """
        count = 0
        ttl = timedelta(hours=self.config.ttl_hours)
        now = datetime.now()

        stale_names = []
        for name, meta in self.metadata.items():
            cached_time = meta.get("cached_at")
            if not cached_time:
                stale_names.append(name)
                continue

            cached_dt = datetime.fromisoformat(cached_time)
            if now - cached_dt >= ttl:
                stale_names.append(name)

        # Remove stale files
        for name in stale_names:
            # Find and remove the file
            for file in self.cache_dir.iterdir():
                if file.stem == name and file.name != self.METADATA_FILE:
                    file.unlink()
                    count += 1
                    break

            # Remove from metadata
            del self.metadata[name]

        if count > 0:
            self._save_metadata()

        return count

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        total_files = len(list(self.cache_dir.glob("*"))) - 1  # Exclude metadata
        total_size = sum(
            f.stat().st_size for f in self.cache_dir.iterdir() if f.name != self.METADATA_FILE
        )

        return {
            "namespace": self.namespace,
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "cache_dir": str(self.cache_dir),
        }
