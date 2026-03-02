#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple Telegram bot: copy‑paste any YouTube link → receive MP3 audio.

Features
--------
* One‑button “Start”.
* Accepts any YouTube link (including the ?si=… tracking part).
* Downloads best audio, converts to MP3 (ffmpeg), sends it.
* If ffmpeg conversion fails, it falls back to sending the original file.
* No generic error messages – you’ll either get the audio or a clear
  “Video not found / private” note.
"""

import os
import re
import logging
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
        "The bot will download the audio and send it back as an MP3 file.",
        reply_markup=markup,
    )


def clean_url(url: str) -> str:
    """Strip any tracking query string (e.g. ?si=…) from the URL."""
    return re.sub(r"\?.*$", "", url.strip())


def download_audio(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Download best audio from YouTube and convert to MP3.
    Returns (path_to_mp3, error_message). If MP3 conversion fails,
    returns the original .m4a/.webm path inside `error_message`.
    """
    ydl_opts = {
        # Preferred audio format (m4a). We'll later convert to MP3.
        "format": "bestaudio[ext=m4a]/bestaudio",
        "outtmpl": "/tmp/%(title)s.%(ext)s",
        "quiet": True,
        "no_warnings": True,
        # Geo‑bypass and realistic headers = avoids many blocks
        "geo_bypass": True,
        "geo_bypass_country": "US",
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        },
        "retries": 5,
        "fragment_retries": 5,
        "socket_timeout": 15,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded = ydl.prepare_filename(info)

            # If we got a .webm (some audio‑only streams), rename to .m4a
            if downloaded.endswith(".webm"):
                new_path = downloaded.replace(".webm", ".m4a")
                os.rename(downloaded, new_path)
                downloaded = new_path

            # Now convert to MP3 using ffmpeg
            mp3_path = downloaded.rsplit(".", 1)[0] + ".mp3"
            ffmpeg_cmd = [
                "ffmpeg",
                "-y",
                "-i",
                downloaded,
                "-codec:a",
                "libmp3lame",
                "-b:a",
                "192k",
                mp3_path,
            ]
            import subprocess

            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            if result.returncode == 0 and os.path.isfile(mp3_path):
                return mp3_path, None
            else:
                # FFmpeg failed – send the original file instead
                logger.warning(f"ffmpeg failed: {result.stderr}")
                return downloaded, "ffmpeg conversion failed"
    except Exception as e:
        logger.error(f"yt‑dlp download error for {url}: {e}")
        return None, str(e)


def handle_message(update: Update, context: CallbackContext) -> None:
    """Receive a YouTube URL, download audio, and send it."""
    raw = update.message.text
    if not raw:
        return

    url = clean_url(raw)

    # --------------------------------------------------------------
    # Basic validation – must be a YouTube URL
    if not ("youtube.com" in url or "youtu.be" in url):
        update.message.reply_text("❌ Please send a valid YouTube URL.")
        return

    status_msg = update.message.reply_text("🔍 Downloading…")

    file_path, error = download_audio(url)

    if not file_path:
        # Very clear user‑friendly message
        if "404" in (error or ""):
            friendly = "❌ Video not found (404)."
        elif "private" in (error or "").lower():
            friendly = "❌ Video is private."
        elif "age" in (error or "").lower() or "restricted" in (error or "").lower():
            friendly = "❌ Age‑restricted or region‑blocked video."
        else:
            friendly = "❌ Could not process the video."
        status_msg.edit_text(friendly)
        logger.info(f"Download failed for {url}: {error}")
        return

    # --------------------------------------------------------------
    # Send the audio file (MP3 if conversion succeeded, otherwise original)
    try:
        with open(file_path, "rb") as audio_file:
            caption = "✅ Here’s your MP3!"
            update.message.reply_audio(
                audio=audio_file,
                title=os.path.splitext(os.path.basename(file_path))[0],
                caption=caption,
            )
        status_msg.edit_text("✅ Done!")
    except Exception as e:
        logger.error(f"Sending file failed: {e}")
        status_msg.edit_text("❌ Could not send the audio file.")
    finally:
        # Clean up temp files
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass


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
