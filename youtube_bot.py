#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telegram → YouTube audio downloader

Features
--------
* Simple "Start" button.
* Accepts a YouTube link (any format, with or without query string).
* Downloads the best audio stream (normally an .m4a file).
* Tries to convert to MP3 with ffmpeg – if that fails it sends the original .m4a.
* All internal errors are logged; the user sees only a short, friendly message.
* Handles geo‑blocked / age‑restricted videos via yt‑dlp options.
"""

import os
import re
import logging
from typing import Optional, Tuple

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

import yt_dlp

# ----------------------------------------------------------------------
# Logging (Railway will capture everything printed here)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Insert your bot token here (keep it secret!)
BOT_TOKEN = "8631686831:AAEBdL6jD3-RTPgNaqgu0AT_ecn15p3WVdg"

# ----------------------------------------------------------------------
def start(update: Update, context: CallbackContext) -> None:
    """Send a welcome message with a one‑button keyboard."""
    btn = KeyboardButton(text="🟢 Send YouTube URL")
    markup = ReplyKeyboardMarkup([[btn]], resize_keyboard=True, one_time_keyboard=True)

    update.message.reply_text(
        "🎧 Welcome! Press the button (or just paste) a YouTube link.\n"
        "The bot will download the audio and return it as an audio file.",
        reply_markup=markup,
    )


# ----------------------------------------------------------------------
def clean_url(url: str) -> str:
    """Strip any tracking query string (e.g. ?si=…) from the URL."""
    return re.sub(r"\?.*$", "", url.strip())


# ----------------------------------------------------------------------
def download_best_audio(youtube_url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Download the best audio stream from a YouTube video.
    Returns (path_to_downloaded_file, error_message).
    The file is usually an .m4a (Telegram can send that directly).
    """
    ydl_opts = {
        # 1️⃣ Get the best audio, preferring .m4a when available
        "format": "bestaudio[ext=m4a]/bestaudio",
        # 2️⃣ Store in /tmp (Railway’s writable directory)
        "outtmpl": "/tmp/%(title)s.%(ext)s",
        # 3️⃣ Silence normal output – we’ll log ourselves
        "quiet": True,
        "no_warnings": True,
        # 4️⃣ Geo‑bypass – many music videos are region‑locked
        "geo_bypass": True,
        "geo_bypass_country": "US",
        # 5️⃣ Realistic browser headers (helps with age‑gate blocks)
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        },
        # 6️⃣ Retry a few times for flaky network conditions
        "retries": 5,
        "fragment_retries": 5,
        "socket_timeout": 15,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            downloaded_file = ydl.prepare_filename(info)  # may end with .m4a or .webm
            # If yt‑dlp gave us a .webm, rename to .m4a for safety (Telegram still accepts it)
            if downloaded_file.endswith(".webm"):
                alt_path = downloaded_file.replace(".webm", ".m4a")
                os.rename(downloaded_file, alt_path)
                downloaded_file = alt_path
            if os.path.isfile(downloaded_file):
                return downloaded_file, None
            else:
                return None, "downloaded file not found"
    except yt_dlp.utils.DownloadError as e:
        # This catches most “video unavailable / age‑restricted / private” cases
        logger.error(f"yt‑dlp DownloadError: {e}")
        return None, str(e)
    except Exception as e:
        logger.error(f"yt‑dlp unexpected error: {e}")
        return None, str(e)


# ----------------------------------------------------------------------
def convert_to_mp3(source_path: str) -> Optional[str]:
    """
    Convert a local audio file (usually .m4a) to MP3 using ffmpeg.
    Returns the absolute path to the MP3 file, or None if conversion fails.
    """
    mp3_path = source_path.rsplit(".", 1)[0] + ".mp3"
    cmd = [
        "ffmpeg",
        "-y",                    # overwrite if exists
        "-i",
        source_path,
        "-codec:a",
        "libmp3lame",
        "-b:a",
        "192k",
        mp3_path,
    ]

    try:
        import subprocess

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and os.path.isfile(mp3_path):
            return mp3_path
        else:
            logger.error(f"ffmpeg failed (code {result.returncode}): {result.stderr}")
            return None
    except Exception as e:
        logger.error(f"ffmpeg exception: {e}")
        return None


# ----------------------------------------------------------------------
def handle_message(update: Update, context: CallbackContext) -> None:
    """Main flow – receive URL → download → (optional) convert → send."""
    raw = update.message.text
    if not raw:
        return

    url = clean_url(raw)

    # --------------------------------------------------------------
    # Basic validation – must be a YouTube URL
    if not ("youtube.com" in url or "youtu.be" in url):
        update.message.reply_text("❌ Please send a valid YouTube URL.")
        return

    # --------------------------------------------------------------
    # Let the user know we are working
    status = update.message.reply_text("🔍 Downloading audio…")

    # --------------------------------------------------------------
    # 1️⃣ Download the best audio (usually .m4a)
    audio_path, error = download_best_audio(url)

    if not audio_path:
        # Friendly classification of the most common error categories
        friendly = "❌ Could not process the video."
        if error:
            lowered = error.lower()
            if "private" in lowered or "unavailable" in lowered:
                friendly = "❌ Video is private or unavailable."
            elif "age" in lowered or "restricted" in lowered:
                friendly = "❌ Age‑restricted or region‑locked video."
            elif "404" in lowered:
                friendly = "❌ Video not found (404)."
        status.edit_text(friendly)
        logger.info(f"Download failed for {url}: {error}")
        return

    # --------------------------------------------------------------
    # 2️⃣ OPTIONAL: try MP3 conversion (only for nicer filename)
    mp3_path = convert_to_mp3(audio_path)
    final_path = mp3_path if mp3_path else audio_path   # fallback to original

    # --------------------------------------------------------------
    # 3️⃣ Send the audio file
    try:
        with open(final_path, "rb") as audio_file:
            title = os.path.splitext(os.path.basename(final_path))[0]
            update.message.reply_audio(
                audio=audio_file,
                title=title,
                caption="✅ Here’s your audio file!",
            )
        status.edit_text("✅ Done!")
    except Exception as e:
        logger.error(f"Sending file failed: {e}")
        status.edit_text("❌ Could not send the audio file.")
    finally:
        # --------------------------------------------------------------
        # Clean up temporary files (both .m4a and .mp3 if they exist)
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
