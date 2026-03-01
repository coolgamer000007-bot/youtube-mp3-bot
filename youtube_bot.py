import os
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, filters
import yt_dlp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8631686831:AAFvy57We-AfDOIAwbdTsyIyjOE7immc4Is"

def start(update, context):
    update.message.reply_text(
        "🎵 YouTube to MP3 Bot!\n\n"
        "Send me a YouTube URL and I'll download it as MP3.\n\n"
        "Example: https://youtu.be/dQw4w9WgXcQ"
    )

def handle_message(update, context):
    text = update.message.text
    
    if 'youtube.com' not in text and 'youtu.be' not in text:
        update.message.reply_text("❌ Please send a YouTube URL")
        return
    
    try:
        msg = update.message.reply_text("🔍 Processing your request...")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': '/tmp/%(title)s.%(ext)s',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(text, download=True)
            filename = ydl.prepare_filename(info)
            mp3_filename = filename.replace('.webm', '.mp3').replace('.m4a', '.mp3')
            
            if os.path.exists(mp3_filename):
                with open(mp3_filename, 'rb') as audio_file:
                    update.message.reply_audio(
                        audio=audio_file,
                        title=info.get('title', 'YouTube Audio')[:64]
                    )
                
                msg.edit_text("✅ Download completed!")
                os.remove(mp3_filename)
            else:
                msg.edit_text("❌ Download failed")
                
    except Exception as e:
        logger.error(f"Error: {e}")
        update.message.reply_text("❌ An error occurred")

def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    updater.start_polling()
    logger.info("🤖 Bot started successfully!")
    updater.idle()

if __name__ == '__main__':
    main()
