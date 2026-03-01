import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOT_TOKEN = "8631686831:AAFvy57We-AfDOIAwbdTsyIyjOE7immc4Is"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎵 Send me a YouTube URL")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if text.startswith('/'):
        return
    
    # Clean the URL (remove tracking parameters like ?si=)
    clean_url = re.sub(r'\?si=.*', '', text)
    
    if not ('youtube.com' in clean_url or 'youtu.be' in clean_url):
        await update.message.reply_text("❌ Send a valid YouTube URL")
        return
    
    try:
        logger.info(f"Processing URL: {clean_url}")
        msg = await update.message.reply_text("🔍 Checking video...")
        
        # yt-dlp configuration for Python 3.13
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '/tmp/%(title)s.%(ext)s',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Get video info first
            info = ydl.extract_info(clean_url, download=False)
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            logger.info(f"Video: {title}, Duration: {duration}s")
            
            # Check if video is too long (>10 minutes)
            if duration > 600:
                await msg.edit_text("❌ Video too long (max 10 minutes)")
                return
            
            await msg.edit_text(f"⬇️ Downloading: {title[:40]}...")
            
            # Download the file
            ydl.download([clean_url])
            
            # Look for the downloaded file
            expected_file = ydl.prepare_filename(info)
            logger.info(f"Expected file: {expected_file}")
            
            # Check various possible file extensions
            possible_files = [
                expected_file,
                expected_file.replace('.webm', '.mp3'),
                expected_file.replace('.m4a', '.mp3'),
            ]
            
            found_file = None
            for file_path in possible_files:
                if os.path.exists(file_path):
                    found_file = file_path
                    file_size = os.path.getsize(file_path)
                    logger.info(f"File found: {found_file} ({file_size} bytes)")
                    break
            
            if found_file and os.path.getsize(found_file) > 1000:
                await msg.edit_text("📤 Sending audio...")
                
                # Send the audio file
                with open(found_file, 'rb') as audio_file:
                    await update.message.reply_audio(
                        audio=audio_file,
                        title=title[:64],
                        duration=duration
                    )
                
                await msg.edit_text("✅ Audio sent!")
                os.remove(found_file)
            else:
                await msg.edit_text("❌ No audio file created")
                
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("❌ Error occurred")

def main():
    logger.info("🤖 Starting YouTube MP3 Bot...")
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()
