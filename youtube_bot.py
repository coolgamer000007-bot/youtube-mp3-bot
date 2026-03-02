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
    update.message.reply_text("Send YouTube URL or song name")

def get_video_title(url):
    """Extract title from YouTube URL without downloading"""
    try:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('title', 'Unknown')
    except:
        return None

def search_youtube(query):
    """Search YouTube and return first result URL"""
    try:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_result = ydl.extract_info(f"ytsearch1:{query}", download=False)
            if search_result and 'entries' in search_result:
                return search_result['entries'][0]['webpage_url']
    except:
        pass
    return None

def handle_message(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    if not text:
        update.message.reply_text("Send YouTube URL or song name")
        return

    try:
        # Determine if it's a URL or search query
        if "youtube.com" in text or "youtu.be" in text:
            # Clean URL
            url = re.sub(r"\?.*$", "", text)
            update.message.reply_text("🔍 Checking video...")
            
            # Try to get title first
            title = get_video_title(url)
            if title:
                update.message.reply_text(f"🎵 Found: {title}")
            else:
                # If direct URL fails, extract title and search instead
                import urllib.parse
                parsed_url = urllib.parse.urlparse(url)
                video_id = None
                if 'youtu.be' in url:
                    video_id = parsed_url.path.split('/')[-1]
                elif 'v=' in url:
                    video_id = urllib.parse.parse_qs(parsed_url.query).get('v', [None])[0]
                
                if video_id:
                    # Search for the video by ID
                    search_url = search_youtube(f"https://youtu.be/{video_id}")
                    if search_url and search_url != url:
                        url = search_url
                        title = get_video_title(url)
                        if title:
                            update.message.reply_text(f"🔄 Found alternative: {title}")
        else:
            # It's a search query
            update.message.reply_text(f"🔍 Searching for: {text}")
            url = search_youtube(text)
            if url:
                title = get_video_title(url)
                if title:
                    update.message.reply_text(f"🎵 Found: {title}")
            else:
                update.message.reply_text("❌ No results found")
                return

        if not url:
            update.message.reply_text("❌ Could not process this video")
            return
            
        update.message.reply_text("⬇️ Downloading audio...")
        
        # Download with maximum compatibility settings
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": "/tmp/audio.%(ext)s",
            "quiet": True,
            "no_warnings": True,
            "geo_bypass": True,
            "geo_bypass_country": "US",
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Find and send the MP3 file
        mp3_files = glob.glob("/tmp/audio.mp3")
        if not mp3_files:
            mp3_files = glob.glob("/tmp/*.mp3")
        
        if mp3_files:
            filepath = mp3_files[0]
            with open(filepath, "rb") as f:
                update.message.reply_audio(audio=f, caption="✅ Here's your MP3!")
            os.remove(filepath)
            update.message.reply_text("✅ Done!")
        else:
            update.message.reply_text("❌ Could not create audio file")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error: {error_msg}")
        update.message.reply_text("❌ Something went wrong. Try a different video.")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    updater.start_polling()
    logger.info("Bot started")

if __name__ == "__main__":
    main()
