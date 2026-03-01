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
        msg = await update.message.reply_text("🔍 Starting...")
        
        # Test connection first
        try:
            import requests
            test_response = requests.head('https://www.youtube.com', timeout=5)
            logger.info(f"YouTube connection test: {test_response.status_code}")
        except Exception as e:
            logger.error(f"Network test failed: {e}")
            await msg.edit_text("❌ Network error")
            return
        
        # Simple yt-dlp configuration
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '/tmp/%(title)s.%(ext)s',
            'quiet': False,
            'no_warnings': False,
            'extractaudio': True,
            'audioformat': 'mp3',
            'noplaylist': True,
        }
        
        try:
            # First get info without downloading
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(text, download=False)
                logger.info(f"Video info success: {info.get('title', 'Unknown')}")
                
                await msg.edit_text(f"⬇️ Downloading: {info.get('title', 'Video')[:40]}...")
                
                # Now download
                ydl.download([text])
                logger.info("Download completed")
                
                # Find the file
                expected_file = ydl.prepare_filename(info)
                expected_mp3 = expected_file.replace('.webm', '.mp3').replace('.m4a', '.mp3')
                logger.info(f"Looking for: {expected_mp3}")
                
                if os.path.exists(expected_mp3):
                    file_size = os.path.getsize(expected_mp3)
                    logger.info(f"MP3 found: {file_size} bytes")
                    
                    await msg.edit_text("📤 Sending...")
                    with open(expected_mp3, 'rb') as f:
                        await update.message.reply_audio(audio=f)
                    await msg.edit_text("✅ Done!")
                    os.remove(expected_mp3)
                else:
                    # Check for original file
                    if os.path.exists(expected_file):
                        logger.info(f"Original file found: {expected_file}")
                        await msg.edit_text("📤 Converting...")
                        with open(expected_file, 'rb') as f:
                            await update.message.reply_audio(audio=f)
                        await msg.edit_text("✅ Done!")
                        os.remove(expected_file)
                    else:
                        logger.error("No file created")
                        await msg.edit_text("❌ No file created")
                        
        except yt_dlp.DownloadError as e:
            logger.error(f"YouTube DL specific error: {str(e)}")
            await msg.edit_text("❌ YouTube error - try different video")
        except Exception as e:
            logger.error(f"Download error details: {str(e)}")
            await msg.edit_text(f"❌ Error: {str(e)[:100]}")
            
    except Exception as e:
        logger.error(f"General error: {str(e)}")
        await update.message.reply_text("❌ Failed")

def main():
    logger.info("🤖 Starting bot...")
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()
