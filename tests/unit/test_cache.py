"""Tests for EmojiCache."""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from mkdocs_external_emojis.models import CacheConfig, EmojiFormat, EmojiInfo
from mkdocs_external_emojis.sync.cache import EmojiCache


class TestEmojiCache:
    """Tests for EmojiCache."""

    @pytest.fixture
    def cache_dir(self, tmp_path: Path) -> Path:
        """Create a temporary cache directory."""
        return tmp_path / "cache"

    @pytest.fixture
    def cache_config(self, cache_dir: Path) -> CacheConfig:
        """Create test cache configuration."""
        return CacheConfig(directory=cache_dir, ttl_hours=24)

    @pytest.fixture
    def cache(self, cache_config: CacheConfig) -> EmojiCache:
        """Create test emoji cache."""
        return EmojiCache(cache_config, namespace="test")

    def test_init_creates_namespace_dir(self, cache_dir: Path, cache_config: CacheConfig) -> None:
        """Test that initialization creates the namespace directory."""
        EmojiCache(cache_config, namespace="myns")
        assert (cache_dir / "myns").exists()

    def test_load_metadata_empty(self, cache: EmojiCache) -> None:
        """Test loading metadata when file doesn't exist."""
        assert cache.metadata == {}

    def test_load_metadata_corrupt(self, cache: EmojiCache) -> None:
        """Test loading corrupt metadata file returns empty dict."""
        cache.metadata_file.write_text("not valid json {{{")
        cache.metadata = cache._load_metadata()
        assert cache.metadata == {}

    def test_save_and_load_metadata(self, cache: EmojiCache) -> None:
        """Test saving and loading metadata."""
        cache.metadata = {"partyparrot": {"url": "https://example.com/partyparrot.gif"}}
        cache._save_metadata()

        # Create new cache instance to force reload
        new_cache = EmojiCache(cache.config, namespace="test")
        assert new_cache.metadata == {"partyparrot": {"url": "https://example.com/partyparrot.gif"}}


class TestGetCachedPath:
    """Tests for _get_cached_path extension detection."""

    @pytest.fixture
    def cache(self, tmp_path: Path) -> EmojiCache:
        """Create test cache."""
        config = CacheConfig(directory=tmp_path / "cache")
        return EmojiCache(config, namespace="test")

    def test_uses_format_when_available(self, cache: EmojiCache) -> None:
        """Test that format from EmojiInfo is used when available."""
        emoji = EmojiInfo(name="cat", url="https://example.com/cat", format=EmojiFormat.GIF)
        path = cache._get_cached_path(emoji)
        assert path.suffix == ".gif"

    def test_extracts_extension_from_url(self, cache: EmojiCache) -> None:
        """Test extension extraction from URL."""
        emoji = EmojiInfo(name="cat", url="https://example.com/emojis/cat.png", format=None)
        path = cache._get_cached_path(emoji)
        assert path.suffix == ".png"

    def test_extracts_svg_from_url(self, cache: EmojiCache) -> None:
        """Test SVG extension extraction from URL."""
        emoji = EmojiInfo(name="icon", url="https://example.com/icons/icon.svg", format=None)
        path = cache._get_cached_path(emoji)
        assert path.suffix == ".svg"

    def test_extracts_webp_from_url(self, cache: EmojiCache) -> None:
        """Test WebP extension extraction from URL."""
        emoji = EmojiInfo(name="modern", url="https://example.com/modern.webp?v=1", format=None)
        path = cache._get_cached_path(emoji)
        assert path.suffix == ".webp"

    def test_defaults_to_png(self, cache: EmojiCache) -> None:
        """Test that unknown extensions default to PNG."""
        emoji = EmojiInfo(name="unknown", url="https://example.com/unknown", format=None)
        path = cache._get_cached_path(emoji)
        assert path.suffix == ".png"

    def test_defaults_to_png_no_url(self, cache: EmojiCache) -> None:
        """Test that missing URL defaults to PNG."""
        emoji = EmojiInfo(name="nourl", url=None, format=None)
        path = cache._get_cached_path(emoji)
        assert path.suffix == ".png"


class TestIsCached:
    """Tests for is_cached TTL logic."""

    @pytest.fixture
    def cache(self, tmp_path: Path) -> EmojiCache:
        """Create test cache with 1 hour TTL."""
        config = CacheConfig(directory=tmp_path / "cache", ttl_hours=1)
        return EmojiCache(config, namespace="test")

    def test_not_cached_when_not_in_metadata(self, cache: EmojiCache) -> None:
        """Test emoji not cached when not in metadata."""
        emoji = EmojiInfo(name="missing", url="https://example.com/missing.png")
        assert cache.is_cached(emoji) is False

    def test_not_cached_when_file_missing(self, cache: EmojiCache) -> None:
        """Test emoji not cached when file doesn't exist."""
        emoji = EmojiInfo(name="nofile", url="https://example.com/nofile.png")
        cache.metadata["nofile"] = {
            "cached_at": datetime.now().isoformat(),
        }
        assert cache.is_cached(emoji) is False

    def test_not_cached_when_no_timestamp(self, cache: EmojiCache) -> None:
        """Test emoji not cached when no cached_at timestamp."""
        emoji = EmojiInfo(name="notime", url="https://example.com/notime.png")
        # Create the file
        (cache.cache_dir / "notime.png").write_bytes(b"fake image")
        cache.metadata["notime"] = {"url": "https://example.com/notime.png"}
        assert cache.is_cached(emoji) is False

    def test_not_cached_when_stale(self, cache: EmojiCache) -> None:
        """Test emoji not cached when TTL expired."""
        emoji = EmojiInfo(name="stale", url="https://example.com/stale.png")
        # Create the file
        (cache.cache_dir / "stale.png").write_bytes(b"fake image")
        # Set cached_at to 2 hours ago (TTL is 1 hour)
        old_time = datetime.now() - timedelta(hours=2)
        cache.metadata["stale"] = {"cached_at": old_time.isoformat()}
        assert cache.is_cached(emoji) is False

    def test_cached_when_fresh(self, cache: EmojiCache) -> None:
        """Test emoji cached when file exists and TTL not expired."""
        emoji = EmojiInfo(name="fresh", url="https://example.com/fresh.png")
        # Create the file
        (cache.cache_dir / "fresh.png").write_bytes(b"fake image")
        # Set cached_at to 30 minutes ago (TTL is 1 hour)
        recent_time = datetime.now() - timedelta(minutes=30)
        cache.metadata["fresh"] = {"cached_at": recent_time.isoformat()}
        assert cache.is_cached(emoji) is True


class TestStore:
    """Tests for store method."""

    @pytest.fixture
    def cache(self, tmp_path: Path) -> EmojiCache:
        """Create test cache."""
        config = CacheConfig(directory=tmp_path / "cache")
        return EmojiCache(config, namespace="test")

    def test_stores_file_and_metadata(self, cache: EmojiCache, tmp_path: Path) -> None:
        """Test that store copies file and updates metadata."""
        emoji = EmojiInfo(name="new", url="https://example.com/new.gif", format=EmojiFormat.GIF)
        source_file = tmp_path / "source.gif"
        source_file.write_bytes(b"GIF89a fake image data")

        cache.store(emoji, source_file, size_bytes=22)

        # Check file was copied
        cached_path = cache.cache_dir / "new.gif"
        assert cached_path.exists()
        assert cached_path.read_bytes() == b"GIF89a fake image data"

        # Check metadata was updated
        assert "new" in cache.metadata
        assert cache.metadata["new"]["url"] == "https://example.com/new.gif"
        assert cache.metadata["new"]["size_bytes"] == 22
        assert "cached_at" in cache.metadata["new"]


class TestClean:
    """Tests for clean method."""

    @pytest.fixture
    def cache(self, tmp_path: Path) -> EmojiCache:
        """Create test cache."""
        config = CacheConfig(directory=tmp_path / "cache")
        return EmojiCache(config, namespace="test")

    def test_removes_all_files_except_metadata(self, cache: EmojiCache) -> None:
        """Test clean removes all emoji files but keeps metadata file."""
        # Create some files
        (cache.cache_dir / "emoji1.png").write_bytes(b"img1")
        (cache.cache_dir / "emoji2.gif").write_bytes(b"img2")
        cache.metadata = {"emoji1": {}, "emoji2": {}}
        cache._save_metadata()

        count = cache.clean()

        assert count == 2
        assert not (cache.cache_dir / "emoji1.png").exists()
        assert not (cache.cache_dir / "emoji2.gif").exists()
        assert cache.metadata_file.exists()  # metadata file still exists
        assert cache.metadata == {}


class TestCleanStale:
    """Tests for clean_stale method."""

    @pytest.fixture
    def cache(self, tmp_path: Path) -> EmojiCache:
        """Create test cache with 1 hour TTL."""
        config = CacheConfig(directory=tmp_path / "cache", ttl_hours=1)
        return EmojiCache(config, namespace="test")

    def test_removes_stale_entries(self, cache: EmojiCache) -> None:
        """Test that stale entries are removed."""
        # Create fresh emoji
        (cache.cache_dir / "fresh.png").write_bytes(b"fresh")
        # Create stale emoji
        (cache.cache_dir / "stale.png").write_bytes(b"stale")

        now = datetime.now()
        cache.metadata = {
            "fresh": {"cached_at": now.isoformat()},
            "stale": {"cached_at": (now - timedelta(hours=2)).isoformat()},
        }
        cache._save_metadata()

        count = cache.clean_stale()

        assert count == 1
        assert (cache.cache_dir / "fresh.png").exists()
        assert not (cache.cache_dir / "stale.png").exists()
        assert "fresh" in cache.metadata
        assert "stale" not in cache.metadata

    def test_removes_entries_without_timestamp(self, cache: EmojiCache) -> None:
        """Test that entries without cached_at are removed."""
        (cache.cache_dir / "notimestamp.png").write_bytes(b"data")
        cache.metadata = {"notimestamp": {"url": "https://example.com"}}
        cache._save_metadata()

        count = cache.clean_stale()

        assert count == 1
        assert not (cache.cache_dir / "notimestamp.png").exists()


class TestGetStats:
    """Tests for get_stats method."""

    @pytest.fixture
    def cache(self, tmp_path: Path) -> EmojiCache:
        """Create test cache."""
        config = CacheConfig(directory=tmp_path / "cache")
        return EmojiCache(config, namespace="test")

    def test_returns_stats(self, cache: EmojiCache) -> None:
        """Test that stats are calculated correctly."""
        # Create some files
        (cache.cache_dir / "emoji1.png").write_bytes(b"x" * 1000)
        (cache.cache_dir / "emoji2.png").write_bytes(b"y" * 2000)
        # Implementation subtracts 1 for metadata file, so ensure it exists
        cache._save_metadata()

        stats = cache.get_stats()

        assert stats["namespace"] == "test"
        assert stats["total_files"] == 2
        assert stats["total_size_bytes"] == 3000
        assert stats["total_size_mb"] == pytest.approx(0.00, abs=0.01)
