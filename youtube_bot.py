import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import yt_dlp

# Enhanced logging
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
            'quiet': False,
        }
    
    async def start(self, update: Update, context: CallbackContext):
        """Handle /start command"""
        try:
            await update.message.reply_text(
                "🎵 YouTube to MP3 Bot! 🎵\n\n"
                "Send me a YouTube URL and I'll convert it to MP3!\n\n"
                "Example: https://youtu.be/dQw4w9WgXcQ\n\n"
                "Bot is ready! 🚀"
            )
        except Exception as e:
            logger.error(f"Start command error: {e}")
    
    async def handle_message(self, update: Update, context: CallbackContext):
        """Handle all text messages"""
        try:
            text = update.message.text
            logger.info(f"Received message: {text}")
            
            # Check if it's a YouTube URL
            if 'youtube.com' in text or 'youtu.be' in text:
                await self.process_youtube_download(update, text)
            else:
                await update.message.reply_text("❌ Please send a YouTube URL")
                
        except Exception as e:
            logger.error(f"Message handling error: {e}")
            await update.message.reply_text("❌ An error occurred.")
    
    async def process_youtube_download(self, update: Update, youtube_url: str):
        """Process YouTube download"""
        try:
            # Send initial message
            processing_msg = await update.message.reply_text("🔍 Checking video...")
            
            # Get video info first
            try:
                with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                    info = ydl.extract_info(youtube_url, download=False)
                    title = info.get('title', 'Unknown Title')
            except:
                await processing_msg.edit_text("❌ Invalid YouTube URL")
                return
            
            # Download
            await processing_msg.edit_text("⬇️ Downloading MP3...")
            
            try:
                with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                    info = ydl.extract_info(youtube_url, download=True)
                    filename = ydl.prepare_filename(info)
                    mp3_filename = filename.replace('.webm', '.mp3').replace('.m4a', '.mp3')
                    
                    if os.path.exists(mp3_filename):
                        # Send the file
                        with open(mp3_filename, 'rb') as audio_file:
                            await update.message.reply_audio(
                                audio=audio_file,
                                title=title
                            )
                        
                        await processing_msg.edit_text("✅ Download completed!")
                        
                        # Clean up
                        os.remove(mp3_filename)
                    else:
                        await processing_msg.edit_text("❌ Download failed")
                        
            except Exception as e:
                await processing_msg.edit_text("❌ Download error")
                logger.error(f"Download error: {e}")
                
        except Exception as e:
            logger.error(f"Process error: {e}")
            await update.message.reply_text("❌ Unexpected error")

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
    logger.info("🤖 Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
