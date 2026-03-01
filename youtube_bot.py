import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import yt_dlp

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Your actual bot token
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
            "🎵 YouTube to MP3 Bot!\n\n"
            "Send me a YouTube URL and I'll convert it to MP3.\n\n"
            "Example: https://youtu.be/dQw4w9WgXcQ"
        )
    
    async def handle_message(self, update: Update, context: CallbackContext):
        text = update.message.text
        
        # Check if it's a YouTube URL
        if not ('youtube.com' in text or 'youtu.be' in text):
            await update.message.reply_text("❌ Please send a YouTube URL")
            return
        
        try:
            # Send processing message
            msg = await update.message.reply_text("🔍 Processing your request...")
            
            # Download as MP3
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(text, download=True)
                filename = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')
                
                # Check if file exists
                if os.path.exists(filename):
                    # Send the audio file
                    with open(filename, 'rb') as audio_file:
                        await update.message.reply_audio(
                            audio=audio_file,
                            title=info.get('title', 'YouTube Audio'),
                            caption=f"🎵 {info.get('title', 'Downloaded Audio')}"
                        )
                    
                    await msg.edit_text("✅ Download completed!")
                    
                    # Clean up
                    os.remove(filename)
                else:
                    await msg.edit_text("❌ File not found after download")
                    
        except Exception as e:
            logger.error(f"Error: {e}")
            await update.message.reply_text("❌ Error processing your request")

def main():
    """Start the bot"""
    logger.info("🚀 Starting YouTube MP3 Bot...")
    
    # Create bot instance
    bot = YouTubeDownloaderBot()
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    # Start polling
    logger.info("🤖 Bot is running and waiting for messages...")
    application.run_polling()

if __name__ == '__main__':
    main()
