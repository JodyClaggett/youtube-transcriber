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
