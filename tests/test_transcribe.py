import sys
from unittest.mock import MagicMock

import pytest

sys.modules["whisper"] = MagicMock()
sys.modules["yt_dlp"] = MagicMock()

from transcribe import slugify, format_markdown


class TestSlugify:
    def test_spaces_become_hyphens(self):
        assert slugify("Hello World") == "Hello-World"

    def test_special_chars_removed(self):
        assert slugify("Hello: World!") == "Hello-World"

    def test_multiple_spaces_collapse(self):
        assert slugify("Hello   World") == "Hello-World"

    def test_leading_trailing_hyphens_stripped(self):
        assert slugify("  Hello World  ") == "Hello-World"

    def test_unicode_title(self):
        result = slugify("Café & Bar")
        assert "-" in result
        assert "&" not in result


class TestFormatMarkdown:
    def _make_markdown(self, **kwargs):
        defaults = dict(
            title="My Video",
            url="https://youtube.com/watch?v=abc",
            channel="Test Channel",
            duration="5:30",
            transcribed_date="2026-05-04",
            transcript="Hello world.",
        )
        defaults.update(kwargs)
        return format_markdown(**defaults)

    def test_title_in_heading(self):
        md = self._make_markdown(title="My Video")
        assert md.startswith("# My Video")

    def test_url_present(self):
        md = self._make_markdown(url="https://youtube.com/watch?v=abc")
        assert "https://youtube.com/watch?v=abc" in md

    def test_channel_present(self):
        md = self._make_markdown(channel="NASA")
        assert "NASA" in md

    def test_duration_present(self):
        md = self._make_markdown(duration="12:34")
        assert "12:34" in md

    def test_date_present(self):
        md = self._make_markdown(transcribed_date="2026-05-04")
        assert "2026-05-04" in md

    def test_transcript_present(self):
        md = self._make_markdown(transcript="The quick brown fox.")
        assert "The quick brown fox." in md

    def test_separator_present(self):
        md = self._make_markdown()
        assert "---" in md
