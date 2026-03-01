import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import yt_dlp

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your bot token
BOT_TOKEN = "8631686831:AAFvy57We-AfDOIAwbdTsyIyjOE7immc4Is"

class YouTubeDownloaderBot:
    def __init__(self):
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': '/tmp/%(title)s.%(ext)s',
        }
    
    async def start(self, update: Update, context: CallbackContext):
        await update.message.reply_text(
            "🎵 YouTube to MP3 Bot 🎵\n\n"
            "Send me a YouTube URL to download as MP3!\n\n"
            "Example: https://youtu.be/dQw4w9WgXcQ"
        )
    
    async def handle_message(self, update: Update, context: CallbackContext):
        text = update.message.text
        
        if not ('youtube.com' in text or 'youtu.be' in text):
            await update.message.reply_text("❌ Send a YouTube URL")
            return
        
        try:
            msg = await update.message.reply_text("🔍 Processing...")
            
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(text, download=True)
                filename = ydl.prepare_filename(info)
                mp3_filename = filename.replace('.webm', '.mp3')
                
                if os.path.exists(mp3_filename):
                    with open(mp3_filename, 'rb') as audio_file:
                        await update.message.reply_audio(audio=audio_file, title=info.get('title', 'Audio'))
                    await msg.edit_text("✅ Done!")
                    os.remove(mp3_filename)
                else:
                    await msg.edit_text("❌ Failed")
                    
        except Exception as e:
            logger.error(f"Error: {e}")
            await update.message.reply_text("❌ Error")

def main():
    logger.info("Starting bot...")
    bot = YouTubeDownloaderBot()
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    application.run_polling()

if __name__ == '__main__':
    main()
