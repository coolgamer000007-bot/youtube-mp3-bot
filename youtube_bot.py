import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import yt_dlp

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration - Only need Telegram token
BOT_TOKEN = "8631686831:AAFvy57We-AfDOIAwbdTsyIyjOE7immc4Is"

class YouTubeDownloaderBot:
    def __init__(self):
        # YouTube download options for MP3
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'writethumbnail': True,  # Download thumbnail
        }
        
    async def start(self, update: Update, context: CallbackContext) -> None:
        """Send welcome message"""
        welcome_text = """
🎵 *YouTube to MP3 Downloader Bot* 🎵

*How to use:*
1. Send me any YouTube music video URL
2. I'll convert it to high-quality MP3
3. Download your audio file instantly!

*Supported URLs:*
- Full YouTube videos
- YouTube Shorts
- YouTube music videos
- Any YouTube link with audio

*Example:* Send a link like:
`https://youtu.be/VIDEO_ID`
or
`https://www.youtube.com/watch?v=VIDEO_ID`

⚠️ *Note:* Download only content you have permission to use.
        """
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: CallbackContext) -> None:
        """Send help message"""
        help_text = """
🤖 *Bot Commands:*
/start - Start the bot
/help - Show this help

*How to download:*
1. Copy a YouTube video URL
2. Paste it here
3. Wait for processing
4. Receive MP3 file

*What I can download:*
(basically any YouTube video with audio)
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    def get_video_info(self, youtube_url):
        """Get video information without downloading"""
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                return {
                    'title': info.get('title', 'Unknown Title'),
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'uploader': info.get('uploader', 'Unknown Artist')
                }
        except Exception as e:
            logger.error(f"Video info error: {e}")
            return None
    
    def download_as_mp3(self, youtube_url):
        """Download YouTube video as MP3"""
        try:
            # Create downloads directory if it doesn't exist
            if not os.path.exists('downloads'):
                os.makedirs('downloads')
            
            # Download the video and convert to MP3
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=True)
                filename = ydl.prepare_filename(info)
                mp3_filename = filename.replace('.webm', '.mp3').replace('.m4a', '.mp3')
                
                return mp3_filename, info.get('title', 'Downloaded Audio')
                
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None, None
    
    async def handle_message(self, update: Update, context: CallbackContext) -> None:
        """Handle incoming YouTube URLs"""
        message_text = update.message.text
        
        # Check if it's a YouTube URL
        if not any(domain in message_text for domain in ['youtube.com', 'youtu.be']):
            await update.message.reply_text(
                "❌ Please send a valid YouTube URL.\n"
                "Example: `https://youtu.be/dQw4w9WgXcQ`",
                parse_mode='Markdown'
            )
            return
        
        await self.process_youtube_download(update, message_text)
    
    async def process_youtube_download(self, update: Update, youtube_url: str) -> None:
        """Process YouTube download request"""
        try:
            # Step 1: Verify URL and get info
            processing_msg = await update.message.reply_text("🔍 Checking video...")
            
            video_info = self.get_video_info(youtube_url)
            if not video_info:
                await processing_msg.edit_text("❌ Invalid YouTube URL or video not available.")
                return
            
            # Step 2: Check duration (avoid very long videos)
            duration = video_info['duration']
            if duration > 3600:  # 1 hour limit
                await processing_msg.edit_text("❌ Video too long (max 1 hour).")
                return
            
            # Step 3: Show video info
            duration_min = duration // 60
            duration_sec = duration % 60
            await processing_msg.edit_text(
                f"🎵 *{video_info['title']}*\n"
                f"👤 *Artist:* {video_info['uploader']}\n"
                f"⏱️ *Duration:* {duration_min}:{duration_sec:02d}\n"
                f"⬇️ *Downloading MP3...*",
                parse_mode='Markdown'
            )
            
            # Step 4: Download as MP3
            mp3_path, actual_title = self.download_as_mp3(youtube_url)
            
            if mp3_path and os.path.exists(mp3_path):
                # Step 5: Send the MP3 file
                file_size = os.path.getsize(mp3_path) / (1024 * 1024)  # Size in MB
                
                with open(mp3_path, 'rb') as audio_file:
                    await update.message.reply_audio(
                        audio=audio_file,
                        title=actual_title,
                        performer=video_info['uploader'],
                        duration=duration,
                        caption=f"🎵 {actual_title}\n💾 Size: {file_size:.1f}MB"
                    )
                
                await processing_msg.edit_text("✅ Download completed!")
                
                # Step 6: Clean up
                os.remove(mp3_path)
                # Remove thumbnail if exists
                thumb_path = mp3_path.replace('.mp3', '.webp')
                if os.path.exists(thumb_path):
                    os.remove(thumb_path)
                    
            else:
                await processing_msg.edit_text("❌ Download failed. Please try again.")
                
        except Exception as e:
            logger.error(f"Process error: {e}")
            await update.message.reply_text("❌ An error occurred. Please try again.")

    async def error_handler(self, update: Update, context: CallbackContext) -> None:
        """Log errors"""
        logger.error(f"Error: {context.error}")

def main():
    """Start the bot."""
    # Create bot instance
    bot = YouTubeDownloaderBot()
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    application.add_error_handler(bot.error_handler)
    
    # Start the bot
    print("🎵 YouTube MP3 Bot is running...")
    print("Press Ctrl+C to stop")
    application.run_polling()

if __name__ == '__main__':
    main()
