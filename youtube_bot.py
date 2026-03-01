import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOT_TOKEN = "8631686831:AAFvy57We-AfDOIAwbdTsyIyjOE7immc4Is"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎵 Send me a YouTube URL")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if text.startswith('/'):
        return
    
    if not ('youtube.com' in text or 'youtu.be' in text):
        await update.message.reply_text("❌ Send a valid YouTube URL")
        return
    
    try:
        logger.info(f"Processing URL: {text}")
        msg = await update.message.reply_text("🔍 Checking video...")
        
        # SIMPLER yt-dlp configuration that actually works
        ydl_opts = {
            # Download best available audio format
            'format': 'bestaudio',
            # Output template
            'outtmpl': '/tmp/%(title)s.%(ext)s',
            # Extract audio to MP3
            'extractaudio': True,
            'audioformat': 'mp3',
            # Audio quality
            'audioquality': '192',
            # Disable age restriction checks
            'age_limit': 99,
            # Skip download if file exists
            'nopart': True,
            # Show progress
            'quiet': False,
            'no_warnings': False,
            # Force IPv4 (sometimes helps)
            'source_address': '0.0.0.0',
            # Skip problematic videos
            'ignoreerrors': False,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # First, test if we can get video info
                info = ydl.extract_info(text, download=False)
                title = info.get('title', 'Unknown')
                logger.info(f"Video info retrieved: {title}")
                
                await msg.edit_text(f"⬇️ Downloading: {title[:50]}...")
                
                # Now download and extract audio
                ydl.download([text])
                
                # File should be created as /tmp/[title].mp3
                # Clean filename for finding
                clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                expected_file = f"/tmp/{clean_title}.mp3"
                
                logger.info(f"Looking for file: {expected_file}")
                
                # Check if file exists
                if os.path.exists(expected_file):
                    file_size = os.path.getsize(expected_file)
                    logger.info(f"File found: {file_size} bytes")
                    
                    if file_size > 1000:  # Ensure file has content
                        await msg.edit_text("📤 Sending audio...")
                        
                        with open(expected_file, 'rb') as audio_file:
                            await update.message.reply_audio(
                                audio=audio_file,
                                title=title[:64],
                                performer="YouTube"
                            )
                        
                        await msg.edit_text("✅ Audio sent successfully!")
                        os.remove(expected_file)
                    else:
                        await msg.edit_text("❌ File is empty")
                        os.remove(expected_file)
                else:
                    # Try alternative approach - download as m4a and convert
                    logger.info("MP3 not found, trying alternative download")
                    await download_alternative(update, msg, text)
                        
        except yt_dlp.DownloadError as e:
            logger.error(f"DownloadError: {e}")
            await msg.edit_text("❌ Download failed - video might be restricted")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            await msg.edit_text("❌ Unexpected error")
            
    except Exception as e:
        logger.error(f"General error: {e}")
        await update.message.reply_text("❌ Failed to process")

async def download_alternative(update: Update, msg, url):
    """Alternative download method"""
    try:
        await msg.edit_text("🔄 Trying alternative method...")
        
        # Download as m4a first, then convert
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio',
            'outtmpl': '/tmp/audio.%(ext)s',
            'quiet': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        # Check for m4a file
        if os.path.exists('/tmp/audio.m4a'):
            await msg.edit_text("📤 Converting to MP3...")
            
            # Convert using ffmpeg
            import subprocess
            result = subprocess.run([
                'ffmpeg', '-i', '/tmp/audio.m4a', 
                '-codec:a', 'libmp3lame', '-b:a', '192k',
                '/tmp/audio.mp3'
            ], capture_output=True)
            
            if result.returncode == 0 and os.path.exists('/tmp/audio.mp3'):
                with open('/tmp/audio.mp3', 'rb') as f:
                    await update.message.reply_audio(audio=f)
                await msg.edit_text("✅ Done!")
                # Cleanup
                for file in ['/tmp/audio.m4a', '/tmp/audio.mp3']:
                    if os.path.exists(file):
                        os.remove(file)
            else:
                await msg.edit_text("❌ Conversion failed")
        else:
            await msg.edit_text("❌ Alternative download failed")
            
    except Exception as e:
        logger.error(f"Alternative method error: {e}")
        await msg.edit_text("❌ All methods failed")

def main():
    logger.info("🚀 Starting YouTube MP3 Bot...")
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()
