import os
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import yt_dlp
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOT_TOKEN = "8631686831:AAFvy57We-AfDOIAwbdTsyIyjOE7immc4Is"

def start(update, context):
    update.message.reply_text("🎵 Send me a YouTube URL")

def handle_message(update, context):
    text = update.message.text.strip()
    
    if text.startswith('/'):
        return
    
    # Clean the URL
    clean_url = re.sub(r'\?si=.*', '', text)
    
    if not ('youtube.com' in clean_url or 'youtu.be' in clean_url):
        update.message.reply_text("❌ Send a valid YouTube URL")
        return
    
    try:
        logger.info(f"Processing URL: {clean_url}")
        msg = update.message.reply_text("🔍 Checking video...")
        
        # Simple yt-dlp configuration
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '/tmp/%(title)s.%(ext)s',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Get video info
            info = ydl.extract_info(clean_url, download=False)
            title = info.get('title', 'Unknown')
            logger.info(f"Video: {title}")
            
            msg.edit_text(f"⬇️ Downloading: {title[:40]}...")
            
            # Download
            ydl.download([clean_url])
            
            # Find the file
            expected_file = ydl.prepare_filename(info)
            logger.info(f"Expected file: {expected_file}")
            
            if os.path.exists(expected_file):
                file_size = os.path.getsize(expected_file)
                logger.info(f"File found: {file_size} bytes")
                
                if file_size > 1000:
                    msg.edit_text("📤 Sending audio...")
                    
                    # Send the file
                    with open(expected_file, 'rb') as audio_file:
                        update.message.reply_audio(audio=audio_file)
                    
                    msg.edit_text("✅ Audio sent!")
                    os.remove(expected_file)
                else:
                    msg.edit_text("❌ File too small")
                    os.remove(expected_file)
            else:
                msg.edit_text("❌ No file created")
                
    except Exception as e:
        logger.error(f"Error: {e}")
        update.message.reply_text("❌ Error occurred")

def main():
    logger.info("🤖 Starting YouTube MP3 Bot...")
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
