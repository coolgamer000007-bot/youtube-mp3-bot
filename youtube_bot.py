import os
import re
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import yt_dlp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 👉 REPLACE WITH YOUR BOT TOKEN
BOT_TOKEN = "8631686831:AAEBdL6jD3-RTPgNaqgu0AT_ecn15p3WVdg"

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Send YouTube URL")

def handle_message(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    if not text or not ("youtube.com" in text or "youtu.be" in text):
        update.message.reply_text("Send valid YouTube URL")
        return

    # Clean URL (remove ?si= etc.)
    url = re.sub(r"\?.*$", "", text)

    try:
        # Download best audio (usually .m4a)
        ydl_opts = {
            "format": "bestaudio",
            "outtmpl": "/tmp/audio.%(ext)s",
            "quiet": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)

        # Send the file
        with open(filepath, "rb") as f:
            update.message.reply_audio(audio=f)
        os.remove(filepath)

    except Exception as e:
        # Show the actual error to the user
        update.message.reply_text(f"Error: {str(e)[:200]}")
        logger.error(f"Download failed for {url}: {e}")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    updater.start_polling()
    logger.info("Bot started")

if __name__ == "__main__":
    main()
