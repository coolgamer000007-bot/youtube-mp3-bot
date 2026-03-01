import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp
import subprocess

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOT_TOKEN = "8631686831:AAFvy57We-AfDOIAwbdTsyIyjOE7immc4Is"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a YouTube URL")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text.startswith('/'):
        return
    
    if 'youtube.com' not in text and 'youtu.be' not in text:
        await update.message.reply_text("Send YouTube URL")
        return
    
    try:
        logger.info(f"Processing: {text}")
        msg = await update.message.reply_text("🔍 Checking video...")
        
        # Test FFmpeg first
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
            logger.info(f"FFmpeg check: {result.returncode}")
            if result.returncode != 0:
                await msg.edit_text("❌ FFmpeg not available")
                return
        except Exception as e:
            logger.error(f"FFmpeg test failed: {e}")
            await msg.edit_text("❌ FFmpeg error")
            return
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': '/tmp/%(title)s.%(ext)s',
            'quiet': False,
        }
        
        await msg.edit_text("⬇️ Downloading audio...")
        
        # Download with error handling
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Test download first
                info = ydl.extract_info(text, download=False)
                title = info.get('title', 'Unknown')
                logger.info(f"Video title: {title}")
                
                # Now download for real
                ydl.download([text])
                
                # Find the downloaded file
                expected_file = f"/tmp/{title}.mp3"
                logger.info(f"Looking for file: {expected_file}")
                
                if os.path.exists(expected_file):
                    file_size = os.path.getsize(expected_file)
                    logger.info(f"File found: {file_size} bytes")
                    
                    if file_size > 0:
                        await msg.edit_text("📤 Sending MP3...")
                        
                        with open(expected_file, 'rb') as audio_file:
                            await update.message.reply_audio(
                                audio=audio_file,
                                title=title[:50],
                                caption=f"🎵 {title}"
                            )
                        
                        await msg.edit_text("✅ Done!")
                        os.remove(expected_file)
                    else:
                        await msg.edit_text("❌ Empty file")
                        os.remove(expected_file)
                else:
                    # Check for alternative files
                    import glob
                    all_mp3 = glob.glob("/tmp/*.mp3")
                    logger.info(f"All MP3 files: {all_mp3}")
                    
                    if all_mp3:
                        latest_file = max(all_mp3, key=os.path.getctime)
                        await msg.edit_text("📤 Sending file...")
                        
                        with open(latest_file, 'rb') as audio_file:
                            await update.message.reply_audio(audio=audio_file)
                        
                        await msg.edit_text("✅ Done!")
                        os.remove(latest_file)
                    else:
                        await msg.edit_text("❌ No MP3 file created")
                        
        except yt_dlp.DownloadError as e:
            logger.error(f"Download error: {e}")
            await msg.edit_text("❌ Download failed")
        except Exception as e:
            logger.error(f"Processing error: {e}")
            await msg.edit_text("❌ Processing error")
            
    except Exception as e:
        logger.error(f"General error: {e}")
        await update.message.reply_text("❌ Error occurred")

def main():
    logger.info("🚀 Starting bot...")
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT, handle_message))
        application.run_polling()
    except Exception as e:
        logger.error(f"Bot failed to start: {e}")

if __name__ == '__main__':
    main()
