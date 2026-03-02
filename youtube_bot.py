#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telegram → YouTube audio downloader with fallback.

Workflow:
1️⃣ User sends a YouTube link.
2️⃣ Bot fetches video info (title) – works even for age‑restricted / region‑blocked videos.
3️⃣ Bot tries to download the original URL.
   • If it succeeds → send audio.
   • If it fails → bot searches YouTube for "<title> audio" and downloads the first public result.
4️⃣ Audio is sent as MP3 (if conversion succeeds) or original .m4a/.webm.
All errors are logged; user sees only a short friendly message.
"""

import os
import re
import logging
from typing import Optional, Tuple

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

import yt_dlp

# ----------------------------------------------------------------------
# Logging (Railway logs will capture everything)
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
        "The bot will download the audio and return it as an audio file.",
        reply_markup=markup,
    )


def clean_url(url: str) -> str:
    """Remove any query string (e.g. ?si=…) from the URL."""
    return re.sub(r"\?.*$", "", url.strip())


# ----------------------------------------------------------------------
def yt_download_info(url: str) -> Tuple[Optional[dict], Optional[str]]:
    """
    Get video info (title, etc.) without downloading.
    Returns (info_dict, error_message).
    """
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
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
            info = ydl.extract_info(url, download=False)
            return info, None
    except Exception as e:
        logger.error(f"yt‑dlp info error for {url}: {e}")
        return None, str(e)


# ----------------------------------------------------------------------
def yt_download_audio(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Download best audio from a YouTube URL.
    Returns (path_to_file, error_message). File is usually .m4a.
    """
    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio",
        "outtmpl": "/tmp/%(title)s.%(ext)s",
        "quiet": True,
        "no_warnings": True,
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
            downloaded_file = ydl.prepare_filename(info)

            # If yt‑dlp gave us a .webm, rename to .m4a – Telegram still plays it.
            if downloaded_file.endswith(".webm"):
                new_path = downloaded_file.replace(".webm", ".m4a")
                os.rename(downloaded_file, new_path)
                downloaded_file = new_path

            if os.path.isfile(downloaded_file):
                return downloaded_file, None
            else:
                return None, "downloaded file not found"
    except Exception as e:
        logger.error(f"yt‑dlp download error for {url}: {e}")
        return None, str(e)


# ----------------------------------------------------------------------
def convert_to_mp3(source_path: str) -> Optional[str]:
    """Convert .m4a (or other audio) to MP3 using ffmpeg."""
    mp3_path = source_path.rsplit(".", 1)[0] + ".mp3"
    cmd = [
        "ffmpeg",
        "-y",
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
            logger.error(f"ffmpeg failed ({result.returncode}): {result.stderr}")
            return None
    except Exception as e:
        logger.error(f"ffmpeg exception: {e}")
        return None


# ----------------------------------------------------------------------
def fallback_search_and_download(title: str) -> Tuple[Optional[str], Optional[str]]:
    """
    If the original URL cannot be downloaded (age‑restricted, region‑blocked, etc.),
    search YouTube for "<title> audio" and download the first public result.
    Returns (path_to_file, error_message).
    """
    search_query = f"{title} audio"
    logger.info(f"Falling back to YouTube search: {search_query}")

    # yt‑dlp search (ytsearch1) – returns first result dict
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
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
            search_res = ydl.extract_info(f"ytsearch1:{search_query}", download=False)
            if not search_res or not search_res.get("entries"):
                return None, "no search results"
            best_url = search_res["entries"][0]["webpage_url"]
    except Exception as e:
        logger.error(f"yt‑dlp search error: {e}")
        return None, str(e)

    # Download the found video (same as normal download)
    return yt_download_audio(best_url)


# ----------------------------------------------------------------------
def handle_message(update: Update, context: CallbackContext) -> None:
    """Main flow – receive URL, download, fallback if needed, send audio."""
    raw = update.message.text
    if not raw:
        return

    url = clean_url(raw)

    # --------------------------------------------------------------
    # Validate that it's a YouTube URL
    if not ("youtube.com" in url or "youtu.be" in url):
        update.message.reply_text("❌ Please send a valid YouTube URL.")
        return

    status = update.message.reply_text("🔍 Getting video info…")

    # --------------------------------------------------------------
    # 1️⃣ Get video title (works even for age‑restricted)
    info, info_err = yt_download_info(url)
    if not info:
        status.edit_text("❌ Could not retrieve video information.")
        logger.info(f"Info fetch failed for {url}: {info_err}")
        return

    title = info.get("title", "unknown title")
    logger.info(f"Video title: {title}")

    # --------------------------------------------------------------
    # 2️⃣ Try to download the original URL
    status.edit_text("⬇️ Downloading audio from original link…")
    audio_path, dl_err = yt_download_audio(url)

    # --------------------------------------------------------------
    # 3️⃣ If original download failed → fallback search
    if not audio_path:
        logger.info(f"Original download failed: {dl_err}")
        status.edit_text("🔁 Original unavailable – searching for an alternative…")
        audio_path, fallback_err = fallback_search_and_download(title)

        if not audio_path:
            # Friendly messages based on failure reason
            friendly = "❌ Could not process the video."
            if fallback_err:
                lowered = fallback_err.lower()
                if "private" in lowered or "unavailable" in lowered:
                    friendly = "❌ Video is private or unavailable."
                elif "age" in lowered or "restricted" in lowered:
                    friendly = "❌ Age‑restricted or region‑blocked video."
                elif "404" in lowered:
                    friendly = "❌ Video not found (404)."
                elif "no search results" in lowered:
                    friendly = "❌ No public alternative found."
            status.edit_text(friendly)
            logger.info(f"Fallback failed for {url}: {fallback_err}")
            return

    # --------------------------------------------------------------
    # 4️⃣ Optional MP3 conversion
    mp3_path = convert_to_mp3(audio_path)
    final_path = mp3_path if mp3_path else audio_path

    # --------------------------------------------------------------
    # 5️⃣ Send the audio file
    try:
        with open(final_path, "rb") as audio_file:
            caption = f"✅ Audio for \"{title}\""
            update.message.reply_audio(
                audio=audio_file,
                title=os.path.splitext(os.path.basename(final_path))[0],
                caption=caption,
            )
        status.edit_text("✅ Done!")
    except Exception as e:
        logger.error(f"Sending file failed: {e}")
        status.edit_text("❌ Could not send the audio file.")
    finally:
        # Clean up any temporary files
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
