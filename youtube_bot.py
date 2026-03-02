#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telegram → YouTube audio downloader.

User sends a YouTube URL.
Bot:
1️⃣ Downloads the best audio stream (normally .m4a).
2️⃣ If ffmpeg succeeds, converts to MP3; otherwise falls back to the original .m4a.
3️⃣ Sends the audio file back as a Telegram audio message.
All internal errors are logged; the user only sees a short friendly message.
"""

import os
import re
import logging
from typing import Optional, Tuple

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

import yt_dlp

# ----------------------------------------------------------------------
# Logging (Railway logs will show the full traceback if something goes wrong)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Bot token – replace with your own (you already have it)
BOT_TOKEN = "8631686831:AAEBdL6jD3-RTPgNaqgu0AT_ecn15p3WVdg"

# ----------------------------------------------------------------------
def start(update: Update, context: CallbackContext) -> None:
    """Send a welcome message with a single button."""
    btn = KeyboardButton(text="🟢 Send YouTube URL")
    markup = ReplyKeyboardMarkup([[btn]], resize_keyboard=True, one_time_keyboard=True)

    update.message.reply_text(
        "🎧 Welcome! Press the button (or just paste) a YouTube link.\n"
        "The bot will download the audio and return it as an audio file.",
        reply_markup=markup,
    )

# ----------------------------------------------------------------------
def clean_url(url: str) -> str:
    """Remove any query string (e.g. ?si=…) from the URL."""
    return re.sub(r"\?.*$", "", url.strip())

# ----------------------------------------------------------------------
def download_best_audio(youtube_url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Download the best audio from YouTube.

    Returns a tuple: (path_to_m4a, error_message)
    * path_to_m4a  – absolute path to the downloaded file (or None)
    * error_message – None if everything went fine, otherwise a short description.
    """
    ydl_opts = {
        # Get the best audio.  Most YouTube music videos provide an .m4a.
        "format": "bestaudio[ext=m4a]/bestaudio",
        # Save to /tmp (Railway’s writable directory)
        "outtmpl": "/tmp/%(title)s.%(ext)s",
        # Silence normal output – we log ourselves.
        "quiet": True,
        "no_warnings": True,
        # Geo‑bypass (many music videos are region‑locked)
        "geo_bypass": True,
        "geo_bypass_country": "US",
        # Use a realistic browser header (helps with age‑gate)
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        },
        # A few retries – helps with flaky network
        "retries": 5,
        "fragment_retries": 5,
        "socket_timeout": 15,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            # The downloaded filename will have .m4a extension.
            downloaded_file = ydl.prepare_filename(info)
            if os.path.isfile(downloaded_file):
                return downloaded_file, None
            else:
                return None, "downloaded file not found"
    except yt_dlp.utils.DownloadError as e:
        # Most common when video is blocked, private, or age‑restricted
        logger.error(f"yt‑dlp DownloadError: {e}")
        return None, str(e)
    except Exception as e:
        logger.error(f"yt‑dlp unexpected error: {e}")
        return None, str(e)

# ----------------------------------------------------------------------
def convert_to_mp3(source_path: str) -> Optional[str]:
    """
    Convert an existing audio file (usually .m4a) to MP3 using ffmpeg.
    Returns the path to the MP3 file, or None if conversion fails.
    """
    mp3_path = source_path.rsplit(".", 1)[0] + ".mp3"
    ffmpeg_cmd = [
        "ffmpeg",
        "-y",                     # overwrite if exists
        "-i", source_path,
        "-codec:a", "libmp3lame",
        "-b:a", "192k",
        mp3_path,
    ]

    try:
        import subprocess
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if result.returncode == 0 and os.path.isfile(mp3_path):
            return mp3_path
        else:
            logger.error(f"ffmpeg failed: {result.stderr}")
            return None
    except Exception as e:
        logger.error(f"ffmpeg exception: {e}")
        return None

# ----------------------------------------------------------------------
def handle_message(update: Update, context: CallbackContext) -> None:
    """Main flow: receive YouTube URL → download audio → send file."""
    raw = update.message.text
    if not raw:
        return

    url = clean_url(raw)

    # ------------------------------------------------------------------
    # 1️⃣ Basic validation – must be a YouTube link
    if not ("youtube.com" in url or "youtu.be" in url):
        update.message.reply_text("❌ Please send a valid YouTube URL.")
        return

    # ------------------------------------------------------------------
    # 2️⃣ Let the user know we are working
    status_msg = update.message.reply_text("🔍 Downloading audio…")

    # ------------------------------------------------------------------
    # 3️⃣ Download the best audio (usually .m4a)
    audio_path, error = download_best_audio(url)

    if not audio_path:
        # Friendly message – we do not expose the full traceback to the user
        friendly = "❌ Could not process the video."
        # If the error looks like a known case, give a slightly better hint
        if error:
            lowered = error.lower()
            if "unavailable" in lowered or "private" in lowered:
                friendly = "❌ Video is private or unavailable."
            elif "age" in lowered or "restricted" in lowered:
                friendly = "❌ Age‑restricted / region‑locked video."
        status_msg.edit_text(friendly)
        logger.info(f"Download failed for {url}: {error}")
        return

    # ------------------------------------------------------------------
    # 4️⃣ Try to convert to MP3 (optional – Telegram accepts .m4a, but MP3 is nicer)
    mp3_path = convert_to_mp3(audio_path)
    final_path = mp3_path if mp3_path else audio_path  # fallback to original

    # ------------------------------------------------------------------
    # 5️⃣ Send the audio file
    try:
        with open(final_path, "rb") as audio_file:
            # Use the filename (without extension) as the title
            title = os.path.splitext(os.path.basename(final_path))[0]
            update.message.reply_audio(
                audio=audio_file,
                title=title,
                caption="✅ Here’s your audio file!",
            )
        status_msg.edit_text("✅ Done!")
    except Exception as e:
        logger.error(f"Sending file failed: {e}")
        status_msg.edit_text("❌ Could not send the audio file.")
    finally:
        # ------------------------------------------------------------------
        # 6️⃣ Clean up any temporary files we created
        for p in (audio_path, mp3_path):
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass

# ----------------------------------------------------------------------
def main() -> None:
    logger.info("🚀 Starting YouTube‑Audio Bot…")
    updater = Updater(BOT_TOKEN, use_context=True)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
