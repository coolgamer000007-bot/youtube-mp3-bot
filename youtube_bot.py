#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telegram bot → YouTube → MP3

1️⃣ User sends a YouTube video URL (any URL that contains youtube.com or youtu.be).
2️⃣ Bot strips tracking parameters (e.g. ?si=…).
3️⃣ Bot uses yt‑dlp to download the *best audio* stream.
4️⃣ Audio is automatically converted to MP3 (ffmpeg handles the conversion).
5️⃣ Bot sends the MP3 file back to the user.

All errors are caught; the user only sees either “✅ Done!” (the MP3) or a brief “❌ Could not process”.
"""

import os
import re
import logging
from typing import Optional

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

import yt_dlp

# ----------------------------------------------------------------------
# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
# INSERT YOUR BOT TOKEN HERE
BOT_TOKEN = "8631686831:AAEBdL6jD3-RTPgNaqgu0AT_ecn15p3WVdg"
# ----------------------------------------------------------------------


def start(update: Update, context: CallbackContext) -> None:
    """Send a welcome message with a single button."""
    btn = KeyboardButton(text="🟢 Send YouTube URL")
    markup = ReplyKeyboardMarkup([[btn]], resize_keyboard=True, one_time_keyboard=True)

    update.message.reply_text(
        "🎧 Welcome! Press the button (or just paste) and send a YouTube link.\n"
        "The bot will download the audio and return it as an MP3 file.",
        reply_markup=markup,
    )


def clean_url(url: str) -> str:
    """Remove any query string (e.g. ?si=…) from the URL."""
    return re.sub(r"\?.*$", "", url.strip())


def download_mp3(youtube_url: str) -> Optional[str]:
    """
    Download the best audio from a YouTube video and convert to MP3.
    Returns the absolute path to the MP3 file, or None on failure.
    """
    ydl_opts = {
        # 1️⃣ Best audio format
        "format": "bestaudio/best",
        # 2️⃣ Where to store the file
        "outtmpl": "/tmp/%(title)s.%(ext)s",
        # 3️⃣ Post‑process: extract → MP3 @ 192kbps
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        # 4️⃣ Silence yt‑dlp output (we log ourselves)
        "quiet": True,
        "no_warnings": True,
        # 5️⃣ Geo‑bypass – many music videos are region‑locked
        "geo_bypass": True,
        "geo_bypass_country": "US",
        # 6️⃣ Realistic browser headers (helps with age‑gate blocks)
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        },
        # 7️⃣ Retry a few times in case of transient network hiccups
        "retries": 5,
        "fragment_retries": 5,
        "socket_timeout": 15,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)

            # After post‑processing the filename ends with .mp3
            mp3_path = ydl.prepare_filename(info).replace(".webm", ".mp3").replace(
                ".m4a", ".mp3"
            )
            if os.path.isfile(mp3_path):
                return mp3_path
            else:
                logger.error("MP3 file not found after download.")
    except Exception as e:
        logger.error(f"yt‑dlp error for URL {youtube_url}: {e}")

    return None


def handle_message(update: Update, context: CallbackContext) -> None:
    """Main flow – receive a YouTube URL, download MP3, send it."""
    raw = update.message.text
    if not raw:
        return

    url = clean_url(raw)

    # ------------------------------------------------------------------
    # Basic validation – accept only YouTube links
    if not ("youtube.com" in url or "youtu.be" in url):
        update.message.reply_text("❌ Please send a valid YouTube URL.")
        return

    # ------------------------------------------------------------------
    # Let the user know we are working (single status message)
    status = update.message.reply_text("🔍 Downloading…")

    mp3_path = download_mp3(url)

    if not mp3_path:
        # Generic, user‑friendly failure message (no stack trace)
        status.edit_text("❌ Could not process the video.")
        return

    # ------------------------------------------------------------------
    # Send the MP3 file
    try:
        with open(mp3_path, "rb") as audio_file:
            # Title is derived from the filename (without .mp3)
            title = os.path.splitext(os.path.basename(mp3_path))[0]
            update.message.reply_audio(
                audio=audio_file,
                title=title,
                caption="✅ Here’s your MP3!",
            )
        status.edit_text("✅ Done!")
    finally:
        # Clean up the temporary file
        if os.path.exists(mp3_path):
            os.remove(mp3_path)


def main() -> None:
    """Start the bot."""
    logger.info("🚀 Starting YouTube → MP3 Bot…")
    updater = Updater(BOT_TOKEN, use_context=True)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(
        MessageHandler(Filters.text & ~Filters.command, handle_message)
    )

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()


