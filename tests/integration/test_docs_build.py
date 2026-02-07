"""Integration tests for mkdocs build with real API calls."""

import subprocess
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

pytestmark = pytest.mark.integration

# Expected emoji references in test.md
# Format: (emoji_name, namespace_prefix)
EXPECTED_EMOJIS = [
    ("partyparrot", None),
    ("partyparrot", "slack"),
    ("shipit", None),
    ("shipit", "slack"),
    ("meow_party", None),
    ("meow_party", "discord"),
    ("stonks", None),
    ("stonks", "discord"),
]


@pytest.fixture(scope="module")
def built_site(project_root):
    """Build the mkdocs site and return the site directory path."""
    site_dir = Path(project_root) / "site"

    # Clean previous build
    if site_dir.exists():
        import shutil

        shutil.rmtree(site_dir)

    # Run mkdocs build
    result = subprocess.run(
        ["uv", "run", "mkdocs", "build"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"mkdocs build failed:\n{result.stderr}"
    assert site_dir.exists(), "Site directory was not created"

    return site_dir


@pytest.fixture(scope="module")
def test_page_html(built_site):
    """Return the parsed HTML of the test page."""
    test_page = built_site / "test" / "index.html"
    assert test_page.exists(), f"Test page not found at {test_page}"

    with open(test_page) as f:
        return BeautifulSoup(f.read(), "html.parser")


class TestDocsBuild:
    """Tests for the mkdocs documentation build."""

    def test_build_succeeds(self, built_site):
        """Verify the mkdocs build completes successfully."""
        assert built_site.exists()
        assert (built_site / "index.html").exists()

    def test_test_page_exists(self, built_site):
        """Verify the test page was built."""
        test_page = built_site / "test" / "index.html"
        assert test_page.exists()


class TestEmojiRendering:
    """Tests for emoji rendering in the built documentation."""

    def test_emoji_images_present(self, test_page_html):
        """Verify emoji images are rendered in the test page."""
        img_tags = test_page_html.find_all("img")
        emoji_images = [
            img for img in img_tags if img.get("class") and "twemoji" in img.get("class", [])
        ]

        # Should have 8 emoji images (4 emojis x 2 syntax variants each)
        assert len(emoji_images) >= 8, (
            f"Expected at least 8 emoji images, found {len(emoji_images)}"
        )

    def test_slack_emojis_have_valid_src(self, test_page_html):
        """Verify Slack emojis have valid image sources."""
        img_tags = test_page_html.find_all("img")

        # Find images with partyparrot or shipit in alt or src
        slack_emojis = [
            img for img in img_tags if any(name in str(img) for name in ["partyparrot", "shipit"])
        ]

        assert len(slack_emojis) >= 4, (
            f"Expected at least 4 Slack emoji images, found {len(slack_emojis)}"
        )

        for img in slack_emojis:
            src = img.get("src", "")
            assert src, f"Emoji image missing src: {img}"
            # Slack emojis should have URLs (either external or cached, possibly with base URL prefix)
            assert "assets/emojis/" in src or src.startswith("http"), (
                f"Unexpected src format: {src}"
            )

    def test_discord_emojis_have_valid_src(self, test_page_html):
        """Verify Discord emojis have valid image sources."""
        img_tags = test_page_html.find_all("img")

        # Find images with meow_party or stonks in alt or src
        discord_emojis = [
            img for img in img_tags if any(name in str(img) for name in ["meow_party", "stonks"])
        ]

        assert len(discord_emojis) >= 4, (
            f"Expected at least 4 Discord emoji images, found {len(discord_emojis)}"
        )

        for img in discord_emojis:
            src = img.get("src", "")
            assert src, f"Emoji image missing src: {img}"
            # Discord emojis should have URLs (either external or cached, possibly with base URL prefix)
            assert "assets/emojis/" in src or src.startswith("http"), (
                f"Unexpected src format: {src}"
            )

    def test_emoji_alt_text(self, test_page_html):
        """Verify emoji images have appropriate title text."""
        img_tags = test_page_html.find_all("img")
        emoji_images = [
            img for img in img_tags if img.get("class") and "twemoji" in img.get("class", [])
        ]

        for img in emoji_images:
            title = img.get("title", "")
            # Title should contain the emoji name in :name: format
            assert title.startswith(":") and title.endswith(":"), (
                f"Emoji title should be in :name: format, got: {title}"
            )
