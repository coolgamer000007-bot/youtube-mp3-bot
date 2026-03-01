import os
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, filters
import yt_dlp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8631686831:AAFvy57We-AfDOIAwbdTsyIyjOE7immc4Is"

def start(update, context):
    update.message.reply_text("🎵 YouTube to MP3 Bot! Send me a YouTube URL.")

def handle_message(update, context):
    text = update.message.text
    
    if 'youtube.com' not in text and 'youtu.be' not in text:
        update.message.reply_text("❌ Send a YouTube URL")
        return
    
    try:
        msg = update.message.reply_text("⬇️ Downloading...")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }],
            'outtmpl': '/tmp/%(title)s.%(ext)s',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(text, download=True)
            filename = ydl.prepare_filename(info).replace('.webm', '.mp3')
            
            if os.path.exists(filename):
                with open(filename, 'rb') as f:
                    update.message.reply_audio(audio=f, title=info.get('title', 'Audio'))
                msg.edit_text("✅ Done!")
                os.remove(filename)
            else:
                msg.edit_text("❌ Failed")
                
    except Exception as e:
        logger.error(f"Error: {e}")
        update.message.reply_text("❌ Error")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
