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


def parse_urls_file(filepath: str) -> list:
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]


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


if __name__ == "__main__":
    main()
