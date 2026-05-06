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

Install dependencies:

    pip install -r requirements.txt

## Usage

### Single video

    python transcribe.py

You will be prompted for a YouTube URL. The transcript is saved as a `.md` file in the same directory.

### Batch mode

Create a text file with one URL per line (blank lines and lines starting with `#` are ignored):

    # My videos
    https://www.youtube.com/watch?v=...
    https://www.youtube.com/watch?v=...

Then run:

    python transcribe.py urls.txt

Each video is processed in sequence. Failed URLs are skipped with an error message and a summary is printed at the end.

## Notes

- First run downloads the Whisper `base` model (~140MB).
- To use a more accurate model, change `WHISPER_MODEL = "base"` in `transcribe.py` to `small`, `medium`, or `large`.
