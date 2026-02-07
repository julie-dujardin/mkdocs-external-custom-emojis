"""Emoji downloader for fetching images from URLs."""

import contextlib
import logging
import tempfile
from collections.abc import Callable
from pathlib import Path

import requests
from PIL import Image

from mkdocs_external_emojis.constants import LOGGER_NAME
from mkdocs_external_emojis.models import EmojiInfo

logger = logging.getLogger(LOGGER_NAME)


class DownloadError(Exception):
    """Error during emoji download."""

    pass


class EmojiDownloader:
    """Downloads and validates emoji images."""

    def __init__(self, max_size_kb: int = 500, timeout: int = 30) -> None:
        """
        Initialize downloader.

        Args:
            max_size_kb: Maximum file size in KB
            timeout: Request timeout in seconds
        """
        self.max_size_kb = max_size_kb
        self.timeout = timeout

    def download(self, emoji: EmojiInfo) -> tuple[Path, int]:
        """
        Download emoji image from URL.

        Args:
            emoji: Emoji to download

        Returns:
            Tuple of (temp_file_path, size_in_bytes)

        Raises:
            DownloadError: If download fails
        """
        if not emoji.url:
            raise DownloadError(f"No URL for emoji: {emoji.name}")

        try:
            response = requests.get(
                emoji.url,
                timeout=self.timeout,
                stream=True,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise DownloadError(f"Failed to download {emoji.name}: {e}") from e

        # Check content length if available
        content_length = response.headers.get("content-length")
        if content_length:
            size_bytes = int(content_length)
            size_kb = size_bytes / 1024

            if size_kb > self.max_size_kb:
                raise DownloadError(
                    f"Emoji {emoji.name} too large: {size_kb:.1f}KB (max: {self.max_size_kb}KB)"
                )

        # Download to temporary file
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=f".{emoji.format.value if emoji.format else 'png'}"
        ) as temp_file:
            try:
                total_size = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        total_size += len(chunk)
                        # Check size while downloading
                        if total_size > self.max_size_kb * 1024:
                            Path(temp_file.name).unlink()
                            raise DownloadError(
                                f"Emoji {emoji.name} exceeds size limit during download"
                            )
                        temp_file.write(chunk)

                temp_path = Path(temp_file.name)

            except Exception as e:
                # Clean up temp file on error
                with contextlib.suppress(Exception):
                    Path(temp_file.name).unlink()
                raise DownloadError(f"Error downloading {emoji.name}: {e}") from e

        # Validate it's actually an image (after file is closed)
        self._validate_image(temp_path)

        return temp_path, total_size

    def _validate_image(self, file_path: Path) -> None:
        """
        Validate that the file is a valid image.

        Args:
            file_path: Path to image file

        Raises:
            DownloadError: If file is not a valid image
        """
        try:
            with Image.open(file_path) as img:
                img.verify()
        except Exception as e:
            raise DownloadError(f"Invalid image file: {e}") from e

    def download_multiple(
        self,
        emojis: list[EmojiInfo],
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> dict[str, tuple[Path, int]]:
        """
        Download multiple emojis.

        Args:
            emojis: List of emojis to download
            progress_callback: Optional callback(emoji_name, current, total)

        Returns:
            Dictionary mapping emoji names to (path, size) tuples
        """
        results: dict[str, tuple[Path, int]] = {}
        total = len(emojis)

        for i, emoji in enumerate(emojis, 1):
            if progress_callback:
                progress_callback(emoji.name, i, total)

            try:
                results[emoji.name] = self.download(emoji)
            except DownloadError as e:
                logger.warning("Failed to download emoji %s: %s", emoji.name, e)
                continue

        return results
