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
        
        # Download with proper settings
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": "/tmp/downloaded_audio.%(ext)s",
            "quiet": True,
            "no_warnings": False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Find the downloaded file (it might have different extensions)
        audio_files = []
        for ext in ['*.mp3', '*.m4a', '*.webm', '*.opus']:
            audio_files.extend(glob.glob(f"/tmp/downloaded_audio.{ext}"))
        
        # If no specific pattern found, look for any audio file in tmp
        if not audio_files:
            audio_files = glob.glob("/tmp/downloaded_audio*")
        
        logger.info(f"Found audio files: {audio_files}")
        
        if audio_files:
            # Get the first file found
            filepath = audio_files[0]
            
            # If it's a weird extension, try to rename it
            if filepath.endswith('.mhtml') or '.mhtml.' in filepath:
                # Try to convert to proper MP3
                new_filepath = filepath.replace('.mhtml', '').replace('..', '.') + '.mp3'
                if new_filepath.endswith('.mp3'):
                    os.rename(filepath, new_filepath)
                    filepath = new_filepath
                else:
                    # Just add .mp3 extension
                    os.rename(filepath, filepath + '.mp3')
                    filepath = filepath + '.mp3'
            
            # Check if file exists and is not empty
            if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:  # At least 1KB
                # Send the file
                with open(filepath, "rb") as f:
                    update.message.reply_audio(audio=f, title=title[:50], caption="✅ Here's your audio!")
                os.remove(filepath)
                update.message.reply_text("✅ Done!")
            else:
                update.message.reply_text("❌ Downloaded file is too small or corrupted")
        else:
            update.message.reply_text("❌ No audio file was created during download")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Download failed for {url}: {error_msg}")
        
        # Provide user-friendly error messages
        if "Sign in to confirm you're not a bot" in error_msg:
            update.message.reply_text("❌ This video requires human verification. Try a different public video.")
        elif "HTTP Error 404" in error_msg:
            update.message.reply_text("❌ Video not found (404)")
        elif "HTTP Error 403" in error_msg or "private" in error_msg.lower():
            update.message.reply_text("❌ Video is private or unavailable")
        elif "format is not available" in error_msg:
            update.message.reply_text("❌ No audio available for this video")
        elif "Precondition check failed" in error_msg:
            update.message.reply_text("❌ YouTube blocked this request")
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
