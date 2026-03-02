#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telegram bot that:
- Shows a simple "Start" button.
- Accepts a YouTube URL (any extra ?si= parameters are ignored).
- Downloads the best audio, converts it to MP3 using ffmpeg,
- Sends the MP3 file back to the user.
"""

import os
import re
import logging
from typing import Optional

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
# NEW BOT TOKEN (replace the old one)
BOT_TOKEN = "8631686831:AAEBdL6jD3-RTPgNaqgu0AT_ecn15p3WVdg"

# ----------------------------------------------------------------------
def start(update: Update, context: CallbackContext) -> None:
    """Send a welcome message with a single button."""
    button = KeyboardButton(text="🟢 Send YouTube URL")
    markup = ReplyKeyboardMarkup([[button]], resize_keyboard=True, one_time_keyboard=True)

    update.message.reply_text(
        "🎧 Welcome! Press the button (or just type) and send a YouTube link.\n"
        "The bot will return the audio as an MP3 file.",
        reply_markup=markup,
    )

# ----------------------------------------------------------------------
def clean_url(url: str) -> str:
    """Strip tracking parameters (e.g. ?si=…) from a YouTube URL."""
    return re.sub(r"\?.*$", "", url.strip())

# ----------------------------------------------------------------------
def download_audio(url: str) -> Optional[str]:
    """
    Download the best audio from a YouTube URL, convert it to MP3,
    and return the absolute path to the created file.
    Returns None on failure.
    """
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "/tmp/%(title)s.%(ext)s",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # After post‑processing the file will be .mp3
            mp3_path = ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".m4a", ".mp3")
            if os.path.isfile(mp3_path):
                return mp3_path
    except Exception as e:
        logger.error(f"yt‑dlp error: {e}")

    return None

# ----------------------------------------------------------------------
def handle_message(update: Update, context: CallbackContext) -> None:
    """Main handler – receives the URL, downloads, sends the MP3."""
    raw = update.message.text
    if not raw:
        return

    url = clean_url(raw)

    # Basic validation – accept only YouTube links
    if not ("youtube.com" in url or "youtu.be" in url):
        update.message.reply_text("❌ Please send a valid YouTube URL.")
        return

    status_msg = update.message.reply_text("⏳ Downloading…")

    mp3_path = download_audio(url)

    if not mp3_path:
        status_msg.edit_text("❌ Download failed – video may be restricted, private, or too long.")
        return

    try:
        with open(mp3_path, "rb") as audio_file:
            update.message.reply_audio(
                audio=audio_file,
                title=os.path.splitext(os.path.basename(mp3_path))[0],
                caption="✅ Here’s your MP3!",
            )
        status_msg.edit_text("✅ Audio sent!")
    finally:
        # Clean up the temporary file
        if os.path.exists(mp3_path):
            os.remove(mp3_path)

# ----------------------------------------------------------------------
def main() -> None:
    """Start the bot."""
    logger.info("🚀 Starting YouTube‑MP3 Bot…")
    updater = Updater(BOT_TOKEN, use_context=True)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
