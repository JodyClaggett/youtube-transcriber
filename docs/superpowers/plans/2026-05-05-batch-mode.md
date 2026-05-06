# Batch Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add batch mode to the CLI so users can pass a text file of URLs and transcribe all of them in one run, while keeping the existing single-URL interactive mode unchanged.

**Architecture:** Extract the single-URL pipeline from `main()` into `process_one(url, output_dir) -> bool`, which returns True/False instead of calling `sys.exit()`. Add `parse_urls_file(filepath) -> list` to read URLs from a file. Update `main()` to detect `sys.argv`: no args = existing interactive mode; one arg = batch mode that loops over URLs and prints a summary.

**Tech Stack:** Python 3.9+, existing project dependencies (no new packages)

---

## File Map

| File | Change |
|---|---|
| `transcribe.py` | Add `process_one()` and `parse_urls_file()`, refactor `main()` |
| `tests/test_transcribe.py` | Add `TestProcessOne` and `TestParseUrlsFile` test classes |

---

### Task 1: Extract `process_one()` from `main()` and test it

**Files:**
- Modify: `transcribe.py` — add `process_one()`, simplify `main()`
- Modify: `tests/test_transcribe.py` — add `TestProcessOne`

- [ ] **Step 1: Update the import line in `tests/test_transcribe.py`**

The current import line (line 10) is:
```python
from transcribe import slugify, format_markdown, get_video_info, download_audio, transcribe_audio
```

Replace it with:
```python
from transcribe import slugify, format_markdown, get_video_info, download_audio, transcribe_audio, process_one
```

- [ ] **Step 2: Append `TestProcessOne` to `tests/test_transcribe.py`**

```python
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
```

- [ ] **Step 3: Run tests — expect failure**

```bash
pytest tests/test_transcribe.py::TestProcessOne -v
```

Expected: FAIL — `ImportError: cannot import name 'process_one'`

- [ ] **Step 4: Add `process_one()` to `transcribe.py`**

Insert the following function between `transcribe_audio()` and `main()` (after line 71, before line 74):

```python
def process_one(url: str, output_dir: str) -> bool:
    audio_path = None
    try:
        print("\nFetching video info...", end=" ", flush=True)
        info = get_video_info(url)
        print(f'"{info["title"]}" by {info["channel"]} ({info["duration"]})')
    except Exception as e:
        print(f"\nError: Could not fetch video info.\n{e}")
        return False

    try:
        print("Downloading audio...", end=" ", flush=True)
        audio_path = download_audio(url)
        print("✓")
        print(f"Transcribing... (using whisper '{WHISPER_MODEL}' model)", end=" ", flush=True)
        transcript = transcribe_audio(audio_path, WHISPER_MODEL)
        print("✓")
    except Exception as e:
        print(f"\nError: {e}")
        return False
    finally:
        if audio_path:
            shutil.rmtree(os.path.dirname(audio_path), ignore_errors=True)

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
    with open(os.path.join(output_dir, filename), "w", encoding="utf-8") as f:
        f.write(markdown)
    print(f"\nSaved: {filename}")
    return True
```

- [ ] **Step 5: Replace `main()` to delegate to `process_one()`**

Replace the entire current `main()` function body with:

```python
def main() -> None:
    _check_ffmpeg()
    script_dir = os.path.dirname(os.path.abspath(__file__))

    print("YouTube Video Transcriber")
    url = input("Enter YouTube URL: ").strip()
    if not url:
        print("Error: No URL provided.")
        sys.exit(1)
    if not process_one(url, script_dir):
        sys.exit(1)
```

- [ ] **Step 6: Run tests — expect pass**

```bash
pytest tests/test_transcribe.py::TestProcessOne -v
```

Expected: All 7 tests PASS.

- [ ] **Step 7: Run full suite to confirm no regressions**

```bash
pytest tests/ -v
```

Expected: All 30 tests PASS.

- [ ] **Step 8: Commit**

```bash
git add transcribe.py tests/test_transcribe.py
git commit -m "refactor: extract process_one() from main()"
```

---

### Task 2: Add `parse_urls_file()` and test it

**Files:**
- Modify: `transcribe.py` — add `parse_urls_file()`
- Modify: `tests/test_transcribe.py` — add `TestParseUrlsFile`

- [ ] **Step 1: Update the import line in `tests/test_transcribe.py`**

The import line currently ends with `process_one`. Add `parse_urls_file`:

```python
from transcribe import slugify, format_markdown, get_video_info, download_audio, transcribe_audio, process_one, parse_urls_file
```

- [ ] **Step 2: Append `TestParseUrlsFile` to `tests/test_transcribe.py`**

```python
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
```

- [ ] **Step 3: Run tests — expect failure**

```bash
pytest tests/test_transcribe.py::TestParseUrlsFile -v
```

Expected: FAIL — `ImportError: cannot import name 'parse_urls_file'`

- [ ] **Step 4: Add `parse_urls_file()` to `transcribe.py`**

Insert the following function between `transcribe_audio()` and `process_one()`:

```python
def parse_urls_file(filepath: str) -> list:
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]
```

- [ ] **Step 5: Run tests — expect pass**

```bash
pytest tests/test_transcribe.py::TestParseUrlsFile -v
```

Expected: All 5 tests PASS.

- [ ] **Step 6: Run full suite**

```bash
pytest tests/ -v
```

Expected: All 35 tests PASS.

- [ ] **Step 7: Commit**

```bash
git add transcribe.py tests/test_transcribe.py
git commit -m "feat: add parse_urls_file()"
```

---

### Task 3: Update `main()` to support batch mode

**Files:**
- Modify: `transcribe.py` — update `main()` with `sys.argv` detection and batch loop

No new tests — `process_one()` and `parse_urls_file()` are already fully tested. `main()` is an orchestrator; its behavior is verified by the smoke test.

- [ ] **Step 1: Replace `main()` with the full two-mode version**

Replace the entire `main()` function body with:

```python
def main() -> None:
    _check_ffmpeg()
    script_dir = os.path.dirname(os.path.abspath(__file__))

    if len(sys.argv) == 1:
        print("YouTube Video Transcriber")
        url = input("Enter YouTube URL: ").strip()
        if not url:
            print("Error: No URL provided.")
            sys.exit(1)
        if not process_one(url, script_dir):
            sys.exit(1)

    elif len(sys.argv) == 2:
        filepath = sys.argv[1]
        if not os.path.isfile(filepath):
            print(f"Error: File not found: {filepath}")
            sys.exit(1)
        urls = parse_urls_file(filepath)
        if not urls:
            print("No URLs found in file.")
            sys.exit(0)
        print(f"YouTube Video Transcriber — Batch Mode ({len(urls)} URLs)")
        succeeded = 0
        failed = 0
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] {url}")
            if process_one(url, script_dir):
                succeeded += 1
            else:
                print("Skipping.")
                failed += 1
        print(f"\nDone: {succeeded} succeeded, {failed} failed.")

    else:
        print("Usage: python transcribe.py [urls_file.txt]")
        sys.exit(1)
```

- [ ] **Step 2: Run full test suite**

```bash
pytest tests/ -v
```

Expected: All 35 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add transcribe.py
git commit -m "feat: add batch mode via urls file argument"
```

- [ ] **Step 4: Push to GitHub**

```bash
git push
```

---

### Task 4: Smoke test

- [ ] **Step 1: Create a test `urls.txt`**

Create `C:\Users\mxz\working\youtube-transcriber\urls.txt` with at least 2 real URLs and 1 invalid entry:

```
# Batch test
https://www.youtube.com/watch?v=<real-short-video>
https://www.youtube.com/watch?v=<another-real-video>
https://not-a-real-url
```

- [ ] **Step 2: Run batch mode**

```bash
python transcribe.py urls.txt
```

Expected output shape:
```
YouTube Video Transcriber — Batch Mode (3 URLs)

[1/3] https://...
Fetching video info... "Video Title" by Channel (2:30)
Downloading audio... ✓
Transcribing... (using whisper 'base' model) ✓

Saved: Video-Title.md

[2/3] https://...
...

[3/3] https://not-a-real-url
Fetching video info...
Error: Could not fetch video info.
...
Skipping.

Done: 2 succeeded, 1 failed.
```

- [ ] **Step 3: Verify single-URL mode still works**

```bash
python transcribe.py
```

Expected: Prompts `Enter YouTube URL:` exactly as before.

- [ ] **Step 4: Test missing file error**

```bash
python transcribe.py missing.txt
```

Expected: `Error: File not found: missing.txt` and clean exit.

- [ ] **Step 5: Final commit**

```bash
git add .
git commit -m "chore: add example urls.txt for batch testing"
git push
```
