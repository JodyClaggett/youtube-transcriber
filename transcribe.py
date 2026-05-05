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
