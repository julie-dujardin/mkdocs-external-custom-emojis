"""Data models for emoji providers and configuration."""

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path, PurePath
from typing import Any, cast
from urllib.parse import urlparse


class ProviderType(StrEnum):
    """Supported emoji provider types."""

    SLACK = "slack"
    DISCORD = "discord"


class EmojiFormat(StrEnum):
    """Supported emoji image formats."""

    SVG = "svg"
    PNG = "png"
    GIF = "gif"
    JPG = "jpg"
    WEBP = "webp"


@dataclass
class EmojiInfo:
    """Information about a single emoji."""

    name: str
    url: str | None  # None for aliases
    alias_of: str | None = None  # Set if this is an alias
    format: EmojiFormat | None = None  # Detected from URL
    size_bytes: int | None = None  # Set after download

    @property
    def is_alias(self) -> bool:
        """Check if this emoji is an alias."""
        return self.alias_of is not None

    @staticmethod
    def _detect_format_from_url(url: str) -> EmojiFormat | None:
        """Detect emoji format from URL path extension."""
        path = urlparse(url).path
        suffix = PurePath(path).suffix.lower().lstrip(".")
        try:
            return EmojiFormat(suffix)
        except ValueError:
            return None

    def get_file_extension(self) -> str:
        """
        Get file extension for this emoji.

        Returns:
            File extension (without dot), defaults to 'png'
        """
        if self.format:
            return self.format.value

        if self.url:
            fmt = self._detect_format_from_url(self.url)
            if fmt:
                return fmt.value

        return "png"

    @classmethod
    def from_url(cls, name: str, url: str) -> "EmojiInfo":
        """Create EmojiInfo from name and URL."""
        return cls(name=name, url=url, format=cls._detect_format_from_url(url))

    @classmethod
    def from_alias(cls, name: str, target: str) -> "EmojiInfo":
        """Create EmojiInfo for an alias."""
        return cls(name=name, url=None, alias_of=target)


@dataclass
class ProviderFilter:
    """Filtering configuration for emoji providers."""

    include_patterns: list[str] = field(default_factory=list)
    exclude_patterns: list[str] = field(default_factory=list)


@dataclass
class ProviderConfig:
    """Configuration for a single emoji provider."""

    type: ProviderType
    namespace: str
    token_env: str
    enabled: bool = True
    tenant_id: str | None = None  # Env var for tenant/server ID (Discord: guild ID)
    filters: ProviderFilter = field(default_factory=ProviderFilter)

    def __post_init__(self) -> None:
        """Validate and normalize configuration."""
        if isinstance(self.type, str):
            self.type = ProviderType(self.type)

        if isinstance(self.filters, dict):
            self.filters = ProviderFilter(**cast("dict[str, Any]", self.filters))


@dataclass
class CacheConfig:
    """Cache configuration."""

    directory: Path = Path(".mkdocs_emoji_cache")
    ttl_hours: int = 24
    clean_on_build: bool = False

    def __post_init__(self) -> None:
        """Normalize paths."""
        if isinstance(self.directory, str):
            self.directory = Path(self.directory)


@dataclass
class EmojiOptions:
    """Global emoji configuration options."""

    namespace_prefix_required: bool = False  # If true, only :<namespace>-<emoji>: works
    max_size_kb: int = 500
    download_timeout: int = 30  # Request timeout in seconds

    def format_emoji_name(self, namespace: str, name: str) -> str:
        """
        Format emoji name with namespace prefix.

        Args:
            namespace: Provider namespace
            name: Emoji name

        Returns:
            Formatted emoji name (always namespace-name format)
        """
        return f"{namespace}-{name}"


@dataclass
class EmojiConfig:
    """Complete emoji configuration."""

    providers: list[ProviderConfig]
    cache: CacheConfig = field(default_factory=CacheConfig)
    emojis: EmojiOptions = field(default_factory=EmojiOptions)

    def __post_init__(self) -> None:
        """Validate and normalize configuration."""
        # Convert dicts to proper types
        if isinstance(self.cache, dict):
            self.cache = CacheConfig(**cast("dict[str, Any]", self.cache))

        if isinstance(self.emojis, dict):
            self.emojis = EmojiOptions(**cast("dict[str, Any]", self.emojis))

        # Convert provider dicts to ProviderConfig objects
        self.providers = [
            ProviderConfig(**cast("dict[str, Any]", p)) if isinstance(p, dict) else p
            for p in self.providers
        ]

    def get_enabled_providers(self) -> list[ProviderConfig]:
        """Get list of enabled providers."""
        return [p for p in self.providers if p.enabled]

    def get_provider_by_namespace(self, namespace: str) -> ProviderConfig | None:
        """Get provider by namespace."""
        for provider in self.providers:
            if provider.namespace == namespace:
                return provider
        return None


@dataclass
class SyncResult:
    """Result of an emoji sync operation."""

    provider: str
    namespace: str
    total_emojis: int
    synced: int
    cached: int
    skipped: int
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Check if sync was successful."""
        return len(self.errors) == 0
