import os
import re
import logging
import glob
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
        
        # Get video info
        ydl_opts_info = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown')
            update.message.reply_text(f"🎵 Found: {title}")
        
        update.message.reply_text("⬇️ Downloading and converting to MP3...")
        
        # Download and convert to MP3
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": "/tmp/audio.%(ext)s",
            "quiet": True,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Look for MP3 file
        mp3_files = glob.glob("/tmp/audio.mp3")
        if not mp3_files:
            # Check for any MP3 files in tmp
            mp3_files = glob.glob("/tmp/*.mp3")
        
        if mp3_files:
            filepath = mp3_files[0]  # Take the first MP3 file
            
            # Send the file
            with open(filepath, "rb") as f:
                update.message.reply_audio(audio=f, title=title[:50], caption="✅ Here's your MP3!")
            os.remove(filepath)
            update.message.reply_text("✅ Done!")
        else:
            update.message.reply_text("❌ Could not create MP3 file")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Download failed for {url}: {error_msg}")
        
        if "Sign in to confirm you're not a bot" in error_msg:
            update.message.reply_text("❌ Video requires human verification")
        elif "HTTP Error 404" in error_msg:
            update.message.reply_text("❌ Video not found")
        elif "HTTP Error 403" in error_msg:
            update.message.reply_text("❌ Video is private/unavailable")
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
