import os
import re
import shutil
import sys
import tempfile
from datetime import date

import whisper
import yt_dlp


def _check_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        print("Error: ffmpeg is not installed or not on your PATH.")
        print("Install it and try again. See README.md for instructions.")
        sys.exit(1)


WHISPER_MODEL = "base"


def slugify(title: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", title)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug.strip("-")


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


def transcribe_audio(audio_path: str, model_size: str = WHISPER_MODEL) -> str:
    model = whisper.load_model(model_size)
    result = model.transcribe(audio_path)
    return result["text"].strip()


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
        if audio_path:
            tmp_dir = os.path.dirname(audio_path)
            shutil.rmtree(tmp_dir, ignore_errors=True)

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


if __name__ == "__main__":
    main()
