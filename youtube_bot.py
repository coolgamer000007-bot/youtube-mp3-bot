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
        update.message.reply_text("🔍 Getting video info...")
        
        # First, try to get video info to check if it exists
        ydl_opts_info = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown')
            update.message.reply_text(f"🎵 Found: {title}")
        
        update.message.reply_text("⬇️ Downloading audio...")
        
        # Try different format options
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": "/tmp/audio.%(ext)s",
            "quiet": True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            filepath = ydl.prepare_filename(info)
        
        # Send the file
        with open(filepath, "rb") as f:
            update.message.reply_audio(audio=f, title=title[:50])
        os.remove(filepath)
        update.message.reply_text("✅ Done!")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Download failed for {url}: {error_msg}")
        
        # Provide user-friendly error messages
        if "HTTP Error 404" in error_msg:
            update.message.reply_text("❌ Video not found (404)")
        elif "HTTP Error 403" in error_msg or "private" in error_msg.lower():
            update.message.reply_text("❌ Video is private or unavailable")
        elif "format is not available" in error_msg:
            update.message.reply_text("❌ No audio available for this video")
        elif "Precondition check failed" in error_msg:
            update.message.reply_text("❌ YouTube blocked this request (try a different video)")
        else:
            update.message.reply_text(f"❌ Error: {error_msg[:100]}")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    updater.start_polling()
    logger.info("Bot started")

if __name__ == "__main__":
    main()
