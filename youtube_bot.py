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

# Your actual bot token for @spotifydownloder07_bot
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
        """Handle /start command"""
        try:
            await update.message.reply_text(
                "🎵 *YouTube to MP3 Bot* 🎵\n\n"
                "Hello! I'm @spotifydownloder07_bot\n\n"
                "Send me any YouTube URL and I'll convert it to MP3!\n\n"
                "*Example:*\n"
                "`https://youtu.be/dQw4w9WgXcQ`\n\n"
                "Ready to download! 🚀",
                parse_mode='Markdown'
            )
            logger.info("Start command handled")
        except Exception as e:
            logger.error(f"Start error: {e}")
    
    async def handle_message(self, update: Update, context: CallbackContext):
        """Handle all text messages"""
        try:
            text = update.message.text
            logger.info(f"Message received: {text}")
            
            # Skip if it's a command
            if text.startswith('/'):
                return
                
            # Check if it's a YouTube URL
            if 'youtube.com' in text or 'youtu.be' in text:
                await self.process_youtube_download(update, text)
            else:
                await update.message.reply_text(
                    "❌ Please send a valid YouTube URL\n\n"
                    "*Examples:*\n"
                    "- `https://youtu.be/dQw4w9WgXcQ`\n"
                    "- `https://www.youtube.com/watch?v=JGwWNGJdvx8`",
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"Message error: {e}")
            await update.message.reply_text("❌ Error processing your message")
    
    async def process_youtube_download(self, update: Update, youtube_url: str):
        """Process YouTube download"""
        try:
            # Step 1: Initial message
            processing_msg = await update.message.reply_text("🔍 Checking video...")
            logger.info(f"Processing: {youtube_url}")
            
            # Step 2: Get video info
            try:
                with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                    info = ydl.extract_info(youtube_url, download=False)
                    title = info.get('title', 'Unknown Title')
                    duration = info.get('duration', 0)
                    
                    # Check duration (max 10 minutes)
                    if duration > 600:
                        await processing_msg.edit_text("❌ Video too long (max 10 minutes)")
                        return
                        
            except Exception as e:
                await processing_msg.edit_text("❌ Invalid YouTube URL")
                logger.error(f"Video info error: {e}")
                return
            
            # Step 3: Download
            await processing_msg.edit_text(f"⬇️ Downloading: {title}")
            
            try:
                with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                    info = ydl.extract_info(youtube_url, download=True)
                    filename = ydl.prepare_filename(info)
                    mp3_filename = filename.replace('.webm', '.mp3').replace('.m4a', '.mp3')
                    
                    if os.path.exists(mp3_filename):
                        # Send audio file
                        with open(mp3_filename, 'rb') as audio_file:
                            await update.message.reply_audio(
                                audio=audio_file,
                                title=title[:64],
                                performer="YouTube",
                                caption=f"🎵 {title}"
                            )
                        
                        await processing_msg.edit_text("✅ Download completed!")
                        
                        # Clean up
                        os.remove(mp3_filename)
                        logger.info("File cleaned up successfully")
                    else:
                        await processing_msg.edit_text("❌ Download failed - file not found")
                        
            except Exception as e:
                await processing_msg.edit_text("❌ Download error occurred")
                logger.error(f"Download error: {e}")
                
        except Exception as e:
            logger.error(f"Process error: {e}")
            await update.message.reply_text("❌ Unexpected error")

def main():
    """Start the bot"""
    try:
        logger.info("🚀 Starting @spotifydownloder07_bot...")
        
        # Verify token
        if not BOT_TOKEN:
            logger.error("❌ Bot token missing")
            return
        
        # Create bot
        bot = YouTubeDownloaderBot()
        
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", bot.start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
        
        # Start bot
        logger.info("🤖 Bot is running and waiting for messages...")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Bot startup failed: {e}")

if __name__ == '__main__':
    main()
