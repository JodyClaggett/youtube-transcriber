# YouTube Transcriber — Design Spec

**Date:** 2026-05-04
**Status:** Approved

---

## Context

The user wants a personal tool that accepts a YouTube URL and produces a clean, readable transcript saved as a Markdown file named after the video. The tool must be simple to run with no API keys required.

---

## Architecture

Single Python script (`transcribe.py`) with a `requirements.txt`. Three logical stages:

1. **Input** — interactive CLI prompt asks the user for a YouTube URL
2. **Download** — `yt-dlp` fetches audio-only stream to a temporary file
3. **Transcribe** — `openai-whisper` (local, no API key) processes the audio
4. **Output** — writes a `.md` file next to the script, named after the video title

No config file, no modules, no web UI. Everything in one script.

### Dependencies

| Package | Purpose |
|---|---|
| `yt-dlp` | Download audio from YouTube |
| `openai-whisper` | Local speech-to-text transcription |
| `ffmpeg` | System-level audio processing (required by both above) |

Whisper model default: `base` (~140MB, good speed/accuracy balance). Changeable by editing one constant in the script.

---

## User Flow

```
$ python transcribe.py

YouTube Video Transcriber
Enter YouTube URL: https://youtube.com/watch?v=...

Fetching video info...  "How to Build a Rocket" by NASA (12:34)
Downloading audio...    ✓
Transcribing...         ✓  (using whisper 'base' model)

Saved: How-to-Build-a-Rocket.md
```

- Audio is downloaded to a temp file and deleted after transcription
- Progress is shown at each stage so the user knows the tool is working
- Filename is derived from the video title: spaces → hyphens, special chars stripped

---

## Output File Format

Filename: `<video-title-slugified>.md` saved in the same directory as `transcribe.py`.

```markdown
# How to Build a Rocket

**Source:** https://youtube.com/watch?v=...
**Channel:** NASA
**Duration:** 12:34
**Transcribed:** 2026-05-04

---

[full transcript text]
```

---

## Error Handling

- Invalid or inaccessible URL → print a clear error message and exit
- `ffmpeg` not installed → detect early and tell the user how to install it
- Whisper model download fails (no internet on first run) → surface the error clearly
- Temp audio file is always cleaned up, even on failure (via `try/finally`)

---

## Project Files

```
youtube-transcriber/
├── transcribe.py        # main script
├── requirements.txt     # yt-dlp, openai-whisper
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-05-04-youtube-transcriber-design.md
```

A `README.md` with setup instructions (install ffmpeg, pip install, run the script) will also be created.

---

## Verification

1. Install dependencies: `pip install -r requirements.txt` and install `ffmpeg`
2. Run `python transcribe.py` and paste a YouTube URL when prompted
3. Confirm the `.md` file is created next to the script with correct title, metadata, and transcript text
4. Test with a short video (~2 min) and a longer one (~15 min) to confirm it works at both scales
5. Test with an invalid URL to confirm the error message is helpful
