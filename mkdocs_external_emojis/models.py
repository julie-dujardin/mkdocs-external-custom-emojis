"""Data models for emoji providers and configuration."""

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, cast


class ProviderType(StrEnum):
    """Supported emoji provider types."""

    SLACK = "slack"
    # Future: DISCORD = "discord", TEAMS = "teams", etc.


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

    @classmethod
    def from_url(cls, name: str, url: str) -> "EmojiInfo":
        """Create EmojiInfo from name and URL."""
        # Detect format from URL
        url_lower = url.lower()
        emoji_format = None

        for fmt in EmojiFormat:
            if f".{fmt.value}" in url_lower:
                emoji_format = fmt
                break

        return cls(name=name, url=url, format=emoji_format)

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

    prefix_format: str = "namespace-name"  # "namespace-name", "namespace_name", or "name-only"
    max_size_kb: int = 500

    def format_emoji_name(self, namespace: str, name: str) -> str:
        """
        Format emoji name according to prefix_format setting.

        Args:
            namespace: Provider namespace
            name: Emoji name

        Returns:
            Formatted emoji name
        """
        if self.prefix_format == "namespace-name":
            return f"{namespace}-{name}"
        elif self.prefix_format == "namespace_name":
            return f"{namespace}_{name}"
        elif self.prefix_format == "name-only":
            return name
        else:
            # Default to namespace-name if invalid format
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
