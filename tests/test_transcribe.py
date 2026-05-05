import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.modules["whisper"] = MagicMock()
sys.modules["yt_dlp"] = MagicMock()

from transcribe import slugify, format_markdown, get_video_info, download_audio, transcribe_audio, process_one, parse_urls_file


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


class TestGetVideoInfo:
    def _fake_info(self):
        return {
            "title": "How to Build a Rocket",
            "uploader": "NASA",
            "duration": 754,  # seconds = 12:34
        }

    def test_returns_title(self):
        with patch("transcribe.yt_dlp.YoutubeDL") as MockYDL:
            instance = MockYDL.return_value.__enter__.return_value
            instance.extract_info.return_value = self._fake_info()
            info = get_video_info("https://youtube.com/watch?v=fake")
        assert info["title"] == "How to Build a Rocket"

    def test_returns_channel(self):
        with patch("transcribe.yt_dlp.YoutubeDL") as MockYDL:
            instance = MockYDL.return_value.__enter__.return_value
            instance.extract_info.return_value = self._fake_info()
            info = get_video_info("https://youtube.com/watch?v=fake")
        assert info["channel"] == "NASA"

    def test_formats_duration(self):
        with patch("transcribe.yt_dlp.YoutubeDL") as MockYDL:
            instance = MockYDL.return_value.__enter__.return_value
            instance.extract_info.return_value = self._fake_info()
            info = get_video_info("https://youtube.com/watch?v=fake")
        assert info["duration"] == "12:34"

    def test_duration_zero_pads_seconds(self):
        fake = self._fake_info()
        fake["duration"] = 65  # 1:05
        with patch("transcribe.yt_dlp.YoutubeDL") as MockYDL:
            instance = MockYDL.return_value.__enter__.return_value
            instance.extract_info.return_value = fake
            info = get_video_info("https://youtube.com/watch?v=fake")
        assert info["duration"] == "1:05"

    def test_missing_uploader_defaults_to_unknown(self):
        fake = {"title": "Test", "duration": 60}
        with patch("transcribe.yt_dlp.YoutubeDL") as MockYDL:
            instance = MockYDL.return_value.__enter__.return_value
            instance.extract_info.return_value = fake
            info = get_video_info("https://youtube.com/watch?v=fake")
        assert info["channel"] == "Unknown"


class TestDownloadAudio:
    def test_returns_path_string(self):
        with patch("transcribe.yt_dlp.YoutubeDL") as MockYDL:
            instance = MockYDL.return_value.__enter__.return_value
            instance.download.return_value = None
            path = download_audio("https://youtube.com/watch?v=fake")
        assert isinstance(path, str)

    def test_path_ends_with_mp3(self):
        with patch("transcribe.yt_dlp.YoutubeDL") as MockYDL:
            instance = MockYDL.return_value.__enter__.return_value
            instance.download.return_value = None
            path = download_audio("https://youtube.com/watch?v=fake")
        assert path.endswith(".mp3")

    def test_each_call_uses_different_temp_dir(self):
        with patch("transcribe.yt_dlp.YoutubeDL") as MockYDL:
            instance = MockYDL.return_value.__enter__.return_value
            instance.download.return_value = None
            path1 = download_audio("https://youtube.com/watch?v=fake")
            path2 = download_audio("https://youtube.com/watch?v=fake")
        assert os.path.dirname(path1) != os.path.dirname(path2)


class TestTranscribeAudio:
    def test_returns_transcript_text(self):
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": "  Hello world.  "}
        with patch("transcribe.whisper.load_model", return_value=mock_model):
            result = transcribe_audio("/fake/audio.mp3")
        assert result == "Hello world."

    def test_uses_specified_model_size(self):
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": "text"}
        with patch("transcribe.whisper.load_model", return_value=mock_model) as mock_load:
            transcribe_audio("/fake/audio.mp3", model_size="small")
        mock_load.assert_called_once_with("small")

    def test_strips_whitespace_from_result(self):
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": "\n\n  Transcript here.  \n"}
        with patch("transcribe.whisper.load_model", return_value=mock_model):
            result = transcribe_audio("/fake/audio.mp3")
        assert result == "Transcript here."


class TestProcessOne:
    def test_returns_true_on_success(self, tmp_path):
        info = {"title": "My Video", "channel": "Test", "duration": "1:00"}
        with patch("transcribe.get_video_info", return_value=info), \
             patch("transcribe.download_audio", return_value="/tmp/fake/audio.mp3"), \
             patch("transcribe.transcribe_audio", return_value="Hello world."), \
             patch("transcribe.shutil.rmtree"):
            result = process_one("https://youtube.com/watch?v=fake", str(tmp_path))
        assert result is True

    def test_writes_markdown_file_on_success(self, tmp_path):
        info = {"title": "My Video", "channel": "Test", "duration": "1:00"}
        with patch("transcribe.get_video_info", return_value=info), \
             patch("transcribe.download_audio", return_value="/tmp/fake/audio.mp3"), \
             patch("transcribe.transcribe_audio", return_value="Hello world."), \
             patch("transcribe.shutil.rmtree"):
            process_one("https://youtube.com/watch?v=fake", str(tmp_path))
        files = list(tmp_path.glob("*.md"))
        assert len(files) == 1

    def test_returns_false_when_video_info_fails(self, tmp_path):
        with patch("transcribe.get_video_info", side_effect=Exception("Not found")):
            result = process_one("https://youtube.com/watch?v=fake", str(tmp_path))
        assert result is False

    def test_returns_false_when_download_fails(self, tmp_path):
        info = {"title": "My Video", "channel": "Test", "duration": "1:00"}
        with patch("transcribe.get_video_info", return_value=info), \
             patch("transcribe.download_audio", side_effect=Exception("Download failed")):
            result = process_one("https://youtube.com/watch?v=fake", str(tmp_path))
        assert result is False

    def test_returns_false_when_transcribe_fails(self, tmp_path):
        info = {"title": "My Video", "channel": "Test", "duration": "1:00"}
        with patch("transcribe.get_video_info", return_value=info), \
             patch("transcribe.download_audio", return_value="/tmp/fake/audio.mp3"), \
             patch("transcribe.transcribe_audio", side_effect=Exception("Transcribe failed")), \
             patch("transcribe.shutil.rmtree"):
            result = process_one("https://youtube.com/watch?v=fake", str(tmp_path))
        assert result is False

    def test_cleans_up_temp_dir_on_success(self, tmp_path):
        info = {"title": "My Video", "channel": "Test", "duration": "1:00"}
        with patch("transcribe.get_video_info", return_value=info), \
             patch("transcribe.download_audio", return_value="/tmp/fake/audio.mp3"), \
             patch("transcribe.transcribe_audio", return_value="text"), \
             patch("transcribe.shutil.rmtree") as mock_rmtree:
            process_one("https://youtube.com/watch?v=fake", str(tmp_path))
        mock_rmtree.assert_called_once()

    def test_cleans_up_temp_dir_on_failure(self, tmp_path):
        info = {"title": "My Video", "channel": "Test", "duration": "1:00"}
        with patch("transcribe.get_video_info", return_value=info), \
             patch("transcribe.download_audio", return_value="/tmp/fake/audio.mp3"), \
             patch("transcribe.transcribe_audio", side_effect=Exception("fail")), \
             patch("transcribe.shutil.rmtree") as mock_rmtree:
            process_one("https://youtube.com/watch?v=fake", str(tmp_path))
        mock_rmtree.assert_called_once()


class TestParseUrlsFile:
    def test_returns_urls(self, tmp_path):
        f = tmp_path / "urls.txt"
        f.write_text("https://youtube.com/watch?v=abc\nhttps://youtube.com/watch?v=def\n")
        assert parse_urls_file(str(f)) == [
            "https://youtube.com/watch?v=abc",
            "https://youtube.com/watch?v=def",
        ]

    def test_ignores_blank_lines(self, tmp_path):
        f = tmp_path / "urls.txt"
        f.write_text("https://youtube.com/watch?v=abc\n\nhttps://youtube.com/watch?v=def\n")
        assert len(parse_urls_file(str(f))) == 2

    def test_ignores_comment_lines(self, tmp_path):
        f = tmp_path / "urls.txt"
        f.write_text("# my videos\nhttps://youtube.com/watch?v=abc\n")
        assert parse_urls_file(str(f)) == ["https://youtube.com/watch?v=abc"]

    def test_empty_file_returns_empty_list(self, tmp_path):
        f = tmp_path / "urls.txt"
        f.write_text("")
        assert parse_urls_file(str(f)) == []

    def test_all_comments_returns_empty_list(self, tmp_path):
        f = tmp_path / "urls.txt"
        f.write_text("# comment 1\n# comment 2\n")
        assert parse_urls_file(str(f)) == []
