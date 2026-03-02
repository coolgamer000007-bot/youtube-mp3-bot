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
        
        # Try with enhanced headers to avoid bot detection
        ydl_opts_info = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            " geo_bypass": True,
            "geo_bypass_country": "US",
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Cache-Control": "max-age=0"
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown')
            update.message.reply_text(f"🎵 Found: {title}")
        
        update.message.reply_text("⬇️ Downloading audio...")
        
        # Download with anti-detection settings
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": "/tmp/audio.%(ext)s",
            "quiet": True,
            "no_warnings": False,
            "geo_bypass": True,
            "geo_bypass_country": "US",
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Cache-Control": "max-age=0"
            },
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Find the MP3 file
        mp3_files = glob.glob("/tmp/audio.mp3")
        if not mp3_files:
            mp3_files = glob.glob("/tmp/*.mp3")
        
        if mp3_files:
            filepath = mp3_files[0]
            
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
            update.message.reply_text("❌ Video has bot protection. Try a different video or check if it's public.")
        elif "HTTP Error 404" in error_msg:
            update.message.reply_text("❌ Video not found")
        elif "HTTP Error 403" in error_msg:
            update.message.reply_text("❌ Video is private/unavailable")
        else:
            update.message.reply_text(f"❌ Error occurred. Try a different video.")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    updater.start_polling()
    logger.info("Bot started")

if __name__ == "__main__":
    main()
