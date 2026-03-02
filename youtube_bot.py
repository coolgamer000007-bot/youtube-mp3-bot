#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple Telegram → YouTube audio downloader.

User sends any YouTube link (including ?si=… tracking part).
Bot:
* downloads the best audio stream (normally an .m4a file)
* sends that file back as a Telegram audio message
* if anything goes wrong, the bot shows a short error message
  (the full error is also written to Railway logs)
"""

import os
import re
import logging
from typing import Optional, Tuple

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

import yt_dlp

# ----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# 👉 INSERT YOUR BOT TOKEN HERE (replace the placeholder)
BOT_TOKEN = "8631686831:AAEBdL6jD3-RTPgNaqgu0AT_ecn15p3WVdg"
# ----------------------------------------------------------------------


def start(update: Update, context: CallbackContext) -> None:
    """Send a welcome message with a single button."""
    btn = KeyboardButton(text="🟢 Send YouTube URL")
    markup = ReplyKeyboardMarkup([[btn]], resize_keyboard=True, one_time_keyboard=True)

    update.message.reply_text(
        "🎧 Welcome! Press the button (or just paste) a YouTube link.\n"
        "The bot will download the audio and send it back as a Telegram audio file.",
        reply_markup=markup,
    )


def clean_url(url: str) -> str:
    """Remove any tracking query string (e.g. ?si=…) from the URL."""
    return re.sub(r"\?.*$", "", url.strip())


def download_audio(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Download the best audio stream from YouTube.
    Returns (path_to_file, error_message). The file will usually be .m4a.
    """
    ydl_opts = {
        # Prefer an m4a audio-only stream, fallback to any best audio.
        "format": "bestaudio[ext=m4a]/bestaudio",
        "outtmpl": "/tmp/%(title)s.%(ext)s",
        "quiet": True,
        "no_warnings": True,
        # Geo‑bypass and a realistic User‑Agent help with region‑locked videos.
        "geo_bypass": True,
        "geo_bypass_country": "US",
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        },
        # A few retries in case of transient network issues.
        "retries": 5,
        "fragment_retries": 5,
        "socket_timeout": 15,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded = ydl.prepare_filename(info)

            # If yt‑dlp gave us a .webm (some audio‑only streams), rename to .m4a.
            if downloaded.endswith(".webm"):
                new_path = downloaded.replace(".webm", ".m4a")
                os.rename(downloaded, new_path)
                downloaded = new_path

            if os.path.isfile(downloaded):
                return downloaded, None
            else:
                return None, "downloaded file not found"
    except Exception as e:
        # Log the full traceback to Railway logs.
        logger.error(f"yt‑dlp download error for {url}: {e}")
        # Return a short, user‑friendly error (first 200 chars).
        return None, str(e*
