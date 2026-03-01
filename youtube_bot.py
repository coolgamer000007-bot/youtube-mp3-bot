import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import yt_dlp

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOT_TOKEN = "8631686831:AAFvy57We-AfDOIAwbdTsyIyjOE7immc4Is"

async def start(update: Update, context):
    await update.message.reply_text("🎵 Send me a YouTube URL")

async def handle_message(update: Update, context):
    text = update.message.text.strip()
    
    if text.startswith('/'):
        return
    
    if not ('youtube.com' in text or 'youtu.be' in text):
        await update.message.reply_text("❌ Send a valid YouTube URL")
        return
    
    try:
        logger.info(f"Processing URL: {text}")
        msg = await update.message.reply_text("🔍 Checking video...")
        
        # Simple yt-dlp configuration for older version
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '/tmp/%(title)s.%(ext)s',
            'extractaudio': True,
            'audioformat': 'mp3',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Get video info first
            info = ydl.extract_info(text, download=False)
            title = info.get('title', 'Unknown')
            logger.info(f"Video info: {title}")
            
            await msg.edit_text(f"⬇️ Downloading: {title[:40]}...")
            
            # Download the file
            ydl.download([text])
            
            # Look for the downloaded file
            expected_file = ydl.prepare_filename(info)
            logger.info(f"Expected file: {expected_file}")
            
            # Check if file exists
            if os.path.exists(expected_file):
                file_size = os.path.getsize(expected_file)
                logger.info(f"File found: {file_size} bytes")
                
                if file_size > 1000:
                    await msg.edit_text("📤 Sending audio...")
                    
                    # Send the audio file
                    with open(expected_file, 'rb') as audio_file:
                        await update.message.reply_audio(audio=audio_file)
                    
                    await msg.edit_text("✅ Audio sent!")
                    os.remove(expected_file)
                else:
                    await msg.edit_text("❌ File too small")
                    os.remove(expected_file)
            else:
                await msg.edit_text("❌ Download failed - no file created")
                
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
