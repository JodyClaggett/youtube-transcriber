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
    pass


def download_audio(url: str) -> str:
    pass


def transcribe_audio(audio_path: str, model_size: str = WHISPER_MODEL) -> str:
    pass


def main() -> None:
    pass


if __name__ == "__main__":
    main()
