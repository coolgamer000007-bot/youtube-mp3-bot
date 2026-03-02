import os
import re
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import yt_dlp

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BOT_TOKEN = "8631686831:AAFvy57We-AfDOIAwbdTsyIyjOE7immc4Is"

def start(update: Update, context: CallbackContext):
    btn = KeyboardButton(text="🟢 Send YouTube URL")
    markup = ReplyKeyboardMarkup([[btn]], resize_keyboard=True, one_time_keyboard=True)
    update.message.reply_text(
        "🎧 Welcome! Press the button (or just type) and send a YouTube link.\n"
        "The bot will return the audio as an MP3.",
        reply_markup=markup,
    )

def clean_url(url: str) -> str:
    """Strip tracking parameters like ?si=…"""
    return re.sub(r"\?.*$", "", url.strip())

def download_audio(url: str) -> str | None:
    """Download best audio, convert to MP3, return full path or None."""
    opts = {
        "format": "bestaudio/best",
        "outtmpl": "/tmp/%(title)s.%(ext)s",
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
        ],
        "quiet": True,
        "no_warnings": True,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            mp3_path = ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".m4a", ".mp3")
            return mp3_path if os.path.isfile(mp3_path) else None
    except Exception as e:
        logger.error(f"yt‑dlp error: {e}")
        return None

def handle_message(update: Update, context: CallbackContext):
    raw = update.message.text
    if not raw:
        return

    url = clean_url(raw)

    if not ("youtube.com" in url or "youtu.be" in url):
        update.message.reply_text("❌ Please send a valid YouTube URL.")
        return

    status_msg = update.message.reply_text("⏳ Downloading…")
    mp3_path = download_audio(url)

    if not mp3_path:
        status_msg.edit_text("❌ Download failed – video may be restricted.")
        return

    try:
        with open(mp3_path, "rb") as f:
            update.message.reply_audio(
                audio=f,
                title=os.path.splitext(os.path.basename(mp3_path))[0],
                caption="✅ Here’s your MP3!",
            )
        status_msg.edit_text("✅ Done!")
    finally:
        if os.path.exists(mp3_path):
            os.remove(mp3_path)

def main():
    logger.info("🚀 Starting YouTube‑MP3 Bot…")
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
