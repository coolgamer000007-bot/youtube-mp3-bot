import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp
import requests

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
        msg = await update.message.reply_text("🔍 Starting download...")
        
        # Simple and reliable yt-dlp configuration
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': '/tmp/%(title)s.%(ext)s',
            'quiet': False,
            'no_warnings': False,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Get video info first
                info = ydl.extract_info(text, download=False)
                title = info.get('title', 'audio')
                duration = info.get('duration', 0)
                
                # Check if video is too long (>15 minutes)
                if duration > 900:
                    await msg.edit_text("❌ Video too long (max 15 minutes)")
                    return
                
                await msg.edit_text(f"⬇️ Downloading: {title[:50]}...")
                
                # Download the file
                ydl.download([text])
                
                # Find the downloaded file
                expected_filename = ydl.prepare_filename(info)
                logger.info(f"Expected file: {expected_filename}")
                
                if os.path.exists(expected_filename):
                    file_size = os.path.getsize(expected_filename)
                    logger.info(f"File size: {file_size} bytes")
                    
                    if file_size > 1000:  # Ensure file has content
                        await msg.edit_text("📤 Sending audio...")
                        
                        # Send whatever format was downloaded (m4a, mp3, etc.)
                        with open(expected_filename, 'rb') as audio_file:
                            await update.message.reply_audio(
                                audio=audio_file,
                                title=title[:64],
                                duration=duration,
                                performer="YouTube"
                            )
                        
                        await msg.edit_text("✅ Audio sent successfully!")
                        os.remove(expected_filename)
                    else:
                        await msg.edit_text("❌ Downloaded file is empty")
                        if os.path.exists(expected_filename):
                            os.remove(expected_filename)
                else:
                    # Try to find any audio files in /tmp
                    import glob
                    audio_files = []
                    for ext in ['*.m4a', '*.mp3', '*.webm', '*.opus']:
                        audio_files.extend(glob.glob(f"/tmp/{ext}"))
                    
                    logger.info(f"All audio files found: {audio_files}")
                    
                    if audio_files:
                        latest_file = max(audio_files, key=os.path.getctime)
                        await msg.edit_text("📤 Sending audio file...")
                        
                        with open(latest_file, 'rb') as audio_file:
                            await update.message.reply_audio(audio=audio_file)
                        
                        await msg.edit_text("✅ Done!")
                        os.remove(latest_file)
                    else:
                        await msg.edit_text("❌ No audio file was created")
                        
        except yt_dlp.DownloadError as e:
            logger.error(f"YouTube DL error: {e}")
            await msg.edit_text("❌ YouTube download error")
        except Exception as e:
            logger.error(f"Download processing error: {e}")
            await msg.edit_text("❌ Processing error")
            
    except Exception as e:
        logger.error(f"General error: {e}")
        await update.message.reply_text("❌ An error occurred")

def main():
    logger.info("🚀 Starting YouTube MP3 Bot...")
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.run_polling()
    except Exception as e:
        logger.error(f"Bot startup failed: {e}")

if __name__ == '__main__':
    main()
