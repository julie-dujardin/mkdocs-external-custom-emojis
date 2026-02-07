"""Tests for base provider filtering and alias resolution."""

import pytest

from mkdocs_external_emojis.models import EmojiInfo, ProviderConfig, ProviderFilter, ProviderType
from mkdocs_external_emojis.providers.base import AbstractEmojiProvider


class ConcreteProvider(AbstractEmojiProvider):
    """Concrete implementation for testing abstract base class methods."""

    def fetch_emojis(self) -> dict[str, EmojiInfo]:
        return {}

    def validate_config(self) -> int:
        return 0

    def get_required_env_vars(self) -> list[str]:
        return []


class TestFilterEmojis:
    """Tests for filter_emojis method."""

    @pytest.fixture
    def sample_emojis(self) -> dict[str, EmojiInfo]:
        """Sample emoji dictionary for testing."""
        return {
            "partyparrot": EmojiInfo.from_url("partyparrot", "https://example.com/partyparrot.gif"),
            "catjam": EmojiInfo.from_url("catjam", "https://example.com/catjam.gif"),
            "party_blob": EmojiInfo.from_url("party_blob", "https://example.com/party_blob.gif"),
            "thumbsup": EmojiInfo.from_url("thumbsup", "https://example.com/thumbsup.png"),
            "thumbsdown": EmojiInfo.from_url("thumbsdown", "https://example.com/thumbsdown.png"),
        }

    def test_no_filters_returns_all(self, sample_emojis: dict[str, EmojiInfo]) -> None:
        """Test that no filters returns all emojis."""
        config = ProviderConfig(
            type=ProviderType.SLACK,
            namespace="test",
            token_env="TOKEN",
        )
        provider = ConcreteProvider(config)

        result = provider.filter_emojis(sample_emojis)

        assert result == sample_emojis

    def test_include_pattern_single(self, sample_emojis: dict[str, EmojiInfo]) -> None:
        """Test single include pattern."""
        config = ProviderConfig(
            type=ProviderType.SLACK,
            namespace="test",
            token_env="TOKEN",
            filters=ProviderFilter(include_patterns=["party*"]),
        )
        provider = ConcreteProvider(config)

        result = provider.filter_emojis(sample_emojis)

        assert set(result.keys()) == {"partyparrot", "party_blob"}

    def test_include_patterns_multiple(self, sample_emojis: dict[str, EmojiInfo]) -> None:
        """Test multiple include patterns."""
        config = ProviderConfig(
            type=ProviderType.SLACK,
            namespace="test",
            token_env="TOKEN",
            filters=ProviderFilter(include_patterns=["party*", "thumbs*"]),
        )
        provider = ConcreteProvider(config)

        result = provider.filter_emojis(sample_emojis)

        assert set(result.keys()) == {"partyparrot", "party_blob", "thumbsup", "thumbsdown"}

    def test_exclude_pattern_single(self, sample_emojis: dict[str, EmojiInfo]) -> None:
        """Test single exclude pattern."""
        config = ProviderConfig(
            type=ProviderType.SLACK,
            namespace="test",
            token_env="TOKEN",
            filters=ProviderFilter(exclude_patterns=["thumbs*"]),
        )
        provider = ConcreteProvider(config)

        result = provider.filter_emojis(sample_emojis)

        assert "thumbsup" not in result
        assert "thumbsdown" not in result
        assert "partyparrot" in result
        assert "catjam" in result

    def test_exclude_patterns_multiple(self, sample_emojis: dict[str, EmojiInfo]) -> None:
        """Test multiple exclude patterns."""
        config = ProviderConfig(
            type=ProviderType.SLACK,
            namespace="test",
            token_env="TOKEN",
            filters=ProviderFilter(exclude_patterns=["thumbs*", "*jam"]),
        )
        provider = ConcreteProvider(config)

        result = provider.filter_emojis(sample_emojis)

        assert set(result.keys()) == {"partyparrot", "party_blob"}

    def test_exclude_takes_precedence_over_include(
        self, sample_emojis: dict[str, EmojiInfo]
    ) -> None:
        """Test that exclude patterns are applied before include patterns."""
        config = ProviderConfig(
            type=ProviderType.SLACK,
            namespace="test",
            token_env="TOKEN",
            filters=ProviderFilter(
                include_patterns=["party*"],
                exclude_patterns=["*blob"],
            ),
        )
        provider = ConcreteProvider(config)

        result = provider.filter_emojis(sample_emojis)

        # party_blob matches include but also matches exclude, so it's excluded
        assert set(result.keys()) == {"partyparrot"}

    def test_exact_match_pattern(self, sample_emojis: dict[str, EmojiInfo]) -> None:
        """Test exact match pattern without wildcards."""
        config = ProviderConfig(
            type=ProviderType.SLACK,
            namespace="test",
            token_env="TOKEN",
            filters=ProviderFilter(include_patterns=["catjam"]),
        )
        provider = ConcreteProvider(config)

        result = provider.filter_emojis(sample_emojis)

        assert set(result.keys()) == {"catjam"}

    def test_question_mark_wildcard(self) -> None:
        """Test ? wildcard matches single character."""
        emojis = {
            "cat1": EmojiInfo.from_url("cat1", "https://example.com/cat1.gif"),
            "cat2": EmojiInfo.from_url("cat2", "https://example.com/cat2.gif"),
            "cat10": EmojiInfo.from_url("cat10", "https://example.com/cat10.gif"),
        }
        config = ProviderConfig(
            type=ProviderType.SLACK,
            namespace="test",
            token_env="TOKEN",
            filters=ProviderFilter(include_patterns=["cat?"]),
        )
        provider = ConcreteProvider(config)

        result = provider.filter_emojis(emojis)

        # cat? matches cat1, cat2 but not cat10
        assert set(result.keys()) == {"cat1", "cat2"}


class TestResolveAliases:
    """Tests for resolve_aliases method."""

    @pytest.fixture
    def provider(self) -> ConcreteProvider:
        """Create test provider."""
        config = ProviderConfig(
            type=ProviderType.SLACK,
            namespace="test",
            token_env="TOKEN",
        )
        return ConcreteProvider(config)

    def test_no_aliases(self, provider: ConcreteProvider) -> None:
        """Test emojis without aliases are unchanged."""
        emojis = {
            "partyparrot": EmojiInfo.from_url("partyparrot", "https://example.com/partyparrot.gif"),
            "catjam": EmojiInfo.from_url("catjam", "https://example.com/catjam.gif"),
        }

        result = provider.resolve_aliases(emojis)

        assert len(result) == 2
        assert result["partyparrot"].url == "https://example.com/partyparrot.gif"
        assert result["catjam"].url == "https://example.com/catjam.gif"

    def test_simple_alias(self, provider: ConcreteProvider) -> None:
        """Test simple alias resolution."""
        emojis = {
            "partyparrot": EmojiInfo.from_url("partyparrot", "https://example.com/partyparrot.gif"),
            "parrot": EmojiInfo.from_alias("parrot", "partyparrot"),
        }

        result = provider.resolve_aliases(emojis)

        assert len(result) == 2
        assert result["parrot"].url == "https://example.com/partyparrot.gif"
        assert result["parrot"].name == "parrot"

    def test_alias_chain(self, provider: ConcreteProvider) -> None:
        """Test alias chain resolution."""
        emojis = {
            "original": EmojiInfo.from_url("original", "https://example.com/original.gif"),
            "alias1": EmojiInfo.from_alias("alias1", "original"),
            "alias2": EmojiInfo.from_alias("alias2", "alias1"),
            "alias3": EmojiInfo.from_alias("alias3", "alias2"),
        }

        result = provider.resolve_aliases(emojis)

        assert len(result) == 4
        # All aliases should resolve to the original URL
        assert result["alias1"].url == "https://example.com/original.gif"
        assert result["alias2"].url == "https://example.com/original.gif"
        assert result["alias3"].url == "https://example.com/original.gif"

    def test_alias_to_missing_target(self, provider: ConcreteProvider) -> None:
        """Test alias to non-existent target is not included."""
        emojis = {
            "partyparrot": EmojiInfo.from_url("partyparrot", "https://example.com/partyparrot.gif"),
            "broken_alias": EmojiInfo.from_alias("broken_alias", "nonexistent"),
        }

        result = provider.resolve_aliases(emojis)

        # Broken alias should not be included
        assert len(result) == 1
        assert "partyparrot" in result
        assert "broken_alias" not in result

    def test_circular_alias_protection(self, provider: ConcreteProvider) -> None:
        """Test that circular aliases don't cause infinite loops."""
        emojis = {
            "a": EmojiInfo.from_alias("a", "b"),
            "b": EmojiInfo.from_alias("b", "c"),
            "c": EmojiInfo.from_alias("c", "a"),  # Circular!
        }

        # Should not hang or crash
        result = provider.resolve_aliases(emojis)

        # None should be resolved since they're all circular
        assert len(result) == 0

    def test_alias_preserves_format(self, provider: ConcreteProvider) -> None:
        """Test that alias resolution preserves the format from target."""
        from mkdocs_external_emojis.models import EmojiFormat

        emojis = {
            "original": EmojiInfo(
                name="original",
                url="https://example.com/original.gif",
                format=EmojiFormat.GIF,
            ),
            "myalias": EmojiInfo.from_alias("myalias", "original"),
        }

        result = provider.resolve_aliases(emojis)

        assert result["myalias"].format == EmojiFormat.GIF
