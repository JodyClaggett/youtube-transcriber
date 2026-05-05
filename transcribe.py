import os
import re
import sys
import tempfile
from datetime import date

import whisper
import yt_dlp

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
    pass


if __name__ == "__main__":
    main()
