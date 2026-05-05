# YouTube Transcriber Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a single-file interactive CLI Python script that downloads audio from a YouTube URL, transcribes it locally with Whisper, and saves a Markdown file named after the video.

**Architecture:** One script (`transcribe.py`) with pure helper functions (slugify, format_markdown) and side-effecting functions (get_video_info, download_audio, transcribe_audio) cleanly separated so they can be unit-tested with mocks. `main()` orchestrates everything with progress output and cleanup on failure.

**Tech Stack:** Python 3.9+, yt-dlp, openai-whisper, pytest, ffmpeg (system dependency)

---

## File Map

| File | Role |
|---|---|
| `transcribe.py` | Single script: all functions + `main()` |
| `requirements.txt` | Runtime deps: yt-dlp, openai-whisper |
| `requirements-dev.txt` | Dev deps: pytest |
| `README.md` | Setup and usage instructions |
| `tests/test_transcribe.py` | Unit tests for all testable functions |

---

### Task 1: Project scaffold

**Files:**
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `README.md`
- Create: `transcribe.py` (skeleton)
- Create: `tests/__init__.py`
- Create: `tests/test_transcribe.py` (skeleton)

- [ ] **Step 1: Create `requirements.txt`**

```
yt-dlp>=2024.1.0
openai-whisper>=20231117
```

- [ ] **Step 2: Create `requirements-dev.txt`**

```
pytest>=7.4
```

- [ ] **Step 3: Create `tests/__init__.py`**

Empty file — just touch it.

- [ ] **Step 4: Create `transcribe.py` skeleton**

```python
import os
import re
import sys
import tempfile
from datetime import date

import whisper
import yt_dlp

WHISPER_MODEL = "base"


def slugify(title: str) -> str:
    pass


def format_markdown(title: str, url: str, channel: str, duration: str, transcribed_date: str, transcript: str) -> str:
    pass


def get_video_info(url: str) -> dict:
    pass


def download_audio(url: str) -> str:
    pass


def transcribe_audio(audio_path: str, model_size: str = WHISPER_MODEL) -> str:
    pass


def main() -> None:
    pass


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Create `tests/test_transcribe.py` skeleton**

```python
import pytest
```

- [ ] **Step 6: Create `README.md`**

```markdown
# YouTube Transcriber

Transcribes a YouTube video to a Markdown file using OpenAI Whisper (runs locally, no API key needed).

## Prerequisites

1. Python 3.9+
2. ffmpeg — required for audio processing

### Install ffmpeg

- **Windows:** `winget install ffmpeg` or download from https://ffmpeg.org/download.html and add to PATH
- **macOS:** `brew install ffmpeg`
- **Linux:** `sudo apt install ffmpeg`

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
python transcribe.py
```

You will be prompted for a YouTube URL. The transcript is saved as a `.md` file in the same directory.

## Notes

- First run downloads the Whisper `base` model (~140MB).
- To use a more accurate model, change `WHISPER_MODEL = "base"` in `transcribe.py` to `small`, `medium`, or `large`.
```

- [ ] **Step 7: Install dev dependencies**

```bash
pip install -r requirements-dev.txt
```

- [ ] **Step 8: Commit scaffold**

```bash
git init
git add .
git commit -m "chore: project scaffold"
```

---

### Task 2: Implement and test `slugify()`

**Files:**
- Modify: `transcribe.py` — implement `slugify()`
- Modify: `tests/test_transcribe.py` — add slugify tests

- [ ] **Step 1: Write failing tests**

Replace `tests/test_transcribe.py` with:

```python
import pytest
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
```

- [ ] **Step 2: Run tests — expect failure**

```bash
pytest tests/test_transcribe.py::TestSlugify -v
```

Expected: FAIL — `TypeError` or `AssertionError` because `slugify` returns `None`.

- [ ] **Step 3: Implement `slugify()`**

In `transcribe.py`, replace the `slugify` stub:

```python
def slugify(title: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", title)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug.strip("-")
```

- [ ] **Step 4: Run tests — expect pass**

```bash
pytest tests/test_transcribe.py::TestSlugify -v
```

Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add transcribe.py tests/test_transcribe.py
git commit -m "feat: implement and test slugify()"
```

---

### Task 3: Implement and test `format_markdown()`

**Files:**
- Modify: `transcribe.py` — implement `format_markdown()`
- Modify: `tests/test_transcribe.py` — add format_markdown tests

- [ ] **Step 1: Write failing tests**

Append to `tests/test_transcribe.py`:

```python
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
```

- [ ] **Step 2: Run tests — expect failure**

```bash
pytest tests/test_transcribe.py::TestFormatMarkdown -v
```

Expected: FAIL — `format_markdown` returns `None`.

- [ ] **Step 3: Implement `format_markdown()`**

In `transcribe.py`, replace the `format_markdown` stub:

```python
def format_markdown(title: str, url: str, channel: str, duration: str, transcribed_date: str, transcript: str) -> str:
    return (
        f"# {title}\n\n"
        f"**Source:** {url}\n"
        f"**Channel:** {channel}\n"
        f"**Duration:** {duration}\n"
        f"**Transcribed:** {transcribed_date}\n\n"
        f"---\n\n"
        f"{transcript}"
    )
```

- [ ] **Step 4: Run tests — expect pass**

```bash
pytest tests/test_transcribe.py::TestFormatMarkdown -v
```

Expected: All 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add transcribe.py tests/test_transcribe.py
git commit -m "feat: implement and test format_markdown()"
```

---

### Task 4: Implement and test `get_video_info()`

**Files:**
- Modify: `transcribe.py` — implement `get_video_info()`
- Modify: `tests/test_transcribe.py` — add get_video_info tests

- [ ] **Step 1: Write failing tests**

Append to `tests/test_transcribe.py`:

```python
from unittest.mock import patch, MagicMock
from transcribe import get_video_info


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
```

- [ ] **Step 2: Run tests — expect failure**

```bash
pytest tests/test_transcribe.py::TestGetVideoInfo -v
```

Expected: FAIL — `get_video_info` returns `None`.

- [ ] **Step 3: Implement `get_video_info()`**

In `transcribe.py`, replace the `get_video_info` stub:

```python
def get_video_info(url: str) -> dict:
    opts = {"quiet": True, "no_warnings": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    duration_secs = info.get("duration", 0)
    minutes, seconds = divmod(duration_secs, 60)
    return {
        "title": info["title"],
        "channel": info.get("uploader", "Unknown"),
        "duration": f"{minutes}:{seconds:02d}",
    }
```

- [ ] **Step 4: Run tests — expect pass**

```bash
pytest tests/test_transcribe.py::TestGetVideoInfo -v
```

Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add transcribe.py tests/test_transcribe.py
git commit -m "feat: implement and test get_video_info()"
```

---

### Task 5: Implement and test `download_audio()`

**Files:**
- Modify: `transcribe.py` — implement `download_audio()`
- Modify: `tests/test_transcribe.py` — add download_audio tests

- [ ] **Step 1: Write failing tests**

Append to `tests/test_transcribe.py`:

```python
import os
from transcribe import download_audio


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
```

- [ ] **Step 2: Run tests — expect failure**

```bash
pytest tests/test_transcribe.py::TestDownloadAudio -v
```

Expected: FAIL — `download_audio` returns `None`.

- [ ] **Step 3: Implement `download_audio()`**

In `transcribe.py`, replace the `download_audio` stub:

```python
def download_audio(url: str) -> str:
    tmp_dir = tempfile.mkdtemp()
    output_template = os.path.join(tmp_dir, "audio.%(ext)s")
    opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
    return os.path.join(tmp_dir, "audio.mp3")
```

- [ ] **Step 4: Run tests — expect pass**

```bash
pytest tests/test_transcribe.py::TestDownloadAudio -v
```

Expected: All 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add transcribe.py tests/test_transcribe.py
git commit -m "feat: implement and test download_audio()"
```

---

### Task 6: Implement and test `transcribe_audio()`

**Files:**
- Modify: `transcribe.py` — implement `transcribe_audio()`
- Modify: `tests/test_transcribe.py` — add transcribe_audio tests

- [ ] **Step 1: Write failing tests**

Append to `tests/test_transcribe.py`:

```python
from transcribe import transcribe_audio


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
```

- [ ] **Step 2: Run tests — expect failure**

```bash
pytest tests/test_transcribe.py::TestTranscribeAudio -v
```

Expected: FAIL — `transcribe_audio` returns `None`.

- [ ] **Step 3: Implement `transcribe_audio()`**

In `transcribe.py`, replace the `transcribe_audio` stub:

```python
def transcribe_audio(audio_path: str, model_size: str = WHISPER_MODEL) -> str:
    model = whisper.load_model(model_size)
    result = model.transcribe(audio_path)
    return result["text"].strip()
```

- [ ] **Step 4: Run tests — expect pass**

```bash
pytest tests/test_transcribe.py::TestTranscribeAudio -v
```

Expected: All 3 tests PASS.

- [ ] **Step 5: Run full test suite**

```bash
pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add transcribe.py tests/test_transcribe.py
git commit -m "feat: implement and test transcribe_audio()"
```

---

### Task 7: Implement `main()` with progress output and error handling

**Files:**
- Modify: `transcribe.py` — implement `main()`

- [ ] **Step 1: Check ffmpeg is available before proceeding**

In `transcribe.py`, add a helper near the top (below imports, above `WHISPER_MODEL`):

```python
import shutil


def _check_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        print("Error: ffmpeg is not installed or not on your PATH.")
        print("Install it and try again. See README.md for instructions.")
        sys.exit(1)
```

- [ ] **Step 2: Implement `main()`**

In `transcribe.py`, replace the `main` stub:

```python
def main() -> None:
    _check_ffmpeg()

    print("YouTube Video Transcriber")
    url = input("Enter YouTube URL: ").strip()
    if not url:
        print("Error: No URL provided.")
        sys.exit(1)

    print("\nFetching video info...", end=" ", flush=True)
    try:
        info = get_video_info(url)
    except Exception as e:
        print(f"\nError: Could not fetch video info.\n{e}")
        sys.exit(1)
    print(f'"{info["title"]}" by {info["channel"]} ({info["duration"]})')

    audio_path = None
    try:
        print("Downloading audio...", end=" ", flush=True)
        audio_path = download_audio(url)
        print("✓")

        print(f"Transcribing... (using whisper '{WHISPER_MODEL}' model)", end=" ", flush=True)
        transcript = transcribe_audio(audio_path, WHISPER_MODEL)
        print("✓")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
    finally:
        if audio_path and os.path.exists(audio_path):
            tmp_dir = os.path.dirname(audio_path)
            os.remove(audio_path)
            if os.path.isdir(tmp_dir):
                os.rmdir(tmp_dir)

    today = date.today().isoformat()
    markdown = format_markdown(
        title=info["title"],
        url=url,
        channel=info["channel"],
        duration=info["duration"],
        transcribed_date=today,
        transcript=transcript,
    )

    filename = slugify(info["title"]) + ".md"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, filename)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"\nSaved: {filename}")
```

- [ ] **Step 3: Run all tests to confirm nothing broken**

```bash
pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 4: Commit**

```bash
git add transcribe.py
git commit -m "feat: implement main() with progress output and error handling"
```

---

### Task 8: Install runtime dependencies and smoke test

**Files:** None — runtime validation only.

- [ ] **Step 1: Install runtime dependencies**

```bash
pip install -r requirements.txt
```

Expected: yt-dlp and openai-whisper install successfully. On first run, Whisper will download the `base` model (~140MB) automatically.

- [ ] **Step 2: Confirm ffmpeg is available**

```bash
ffmpeg -version
```

Expected: Prints ffmpeg version info. If not found, follow README install steps.

- [ ] **Step 3: Run with a short test video**

```bash
python transcribe.py
```

When prompted, enter a short YouTube video URL (under 3 minutes to keep the test fast). Example of what to expect:

```
YouTube Video Transcriber
Enter YouTube URL: https://www.youtube.com/watch?v=<your-test-url>

Fetching video info... "Video Title Here" by Channel Name (2:45)
Downloading audio... ✓
Transcribing... (using whisper 'base' model) ✓

Saved: Video-Title-Here.md
```

- [ ] **Step 4: Verify output file**

Open the generated `.md` file and confirm:
- Title heading matches the video
- Source URL is correct
- Channel and duration are present
- Transcript text is readable and sensible

- [ ] **Step 5: Test error handling — invalid URL**

```bash
python transcribe.py
```

Enter `not-a-url` when prompted. Expected output:

```
Fetching video info...
Error: Could not fetch video info.
<yt-dlp error message>
```

Script exits cleanly with no stack trace shown to the user.

- [ ] **Step 6: Final commit**

```bash
git add .
git commit -m "feat: youtube transcriber complete"
```
