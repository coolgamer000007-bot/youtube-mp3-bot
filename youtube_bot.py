import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp
import glob

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
        msg = await update.message.reply_text("🔍 Processing...")
        
        # Working yt-dlp configuration
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': '/tmp/%(title)s.%(ext)s',
            'writethumbnail': False,
            'embedthumbnail': False,
            'noplaylist': True,
        }
        
        await msg.edit_text("⬇️ Downloading...")
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Download the video
                info = ydl.extract_info(text, download=True)
                logger.info(f"Download completed for: {info.get('title', 'Unknown')}")
                
                # Look for any MP3 files in /tmp
                mp3_files = glob.glob("/tmp/*.mp3")
                logger.info(f"Found MP3 files: {mp3_files}")
                
                if mp3_files:
                    # Get the most recent MP3 file
                    latest_file = max(mp3_files, key=os.path.getctime)
                    file_size = os.path.getsize(latest_file)
                    logger.info(f"Selected file: {latest_file} ({file_size} bytes)")
                    
                    if file_size > 1000:  # Ensure file has content
                        await msg.edit_text("📤 Sending...")
                        
                        with open(latest_file, 'rb') as audio_file:
                            await update.message.reply_audio(
                                audio=audio_file,
                                title=os.path.basename(latest_file)[:-4]  # Remove .mp3
                            )
                        
                        await msg.edit_text("✅ Done!")
                        os.remove(latest_file)
                    else:
                        await msg.edit_text("❌ File too small")
                        if os.path.exists(latest_file):
                            os.remove(latest_file)
                else:
                    # Also check for .m4a files (sometimes created instead)
                    m4a_files = glob.glob("/tmp/*.m4a")
                    webm_files = glob.glob("/tmp/*.webm")
                    logger.info(f"M4A files: {m4a_files}")
                    logger.info(f"WEBM files: {webm_files}")
                    
                    # Try to manually convert if MP3 not created
                    if m4a_files:
                        latest_m4a = max(m4a_files, key=os.path.getctime)
                        mp3_path = latest_m4a.replace('.m4a', '.mp3')
                        
                        # Convert using ffmpeg
                        import subprocess
                        result = subprocess.run([
                            'ffmpeg', '-i', latest_m4a, '-codec:a', 'libmp3lame', 
                            '-b:a', '192k', mp3_path
                        ], capture_output=True)
                        
                        if result.returncode == 0 and os.path.exists(mp3_path):
                            await msg.edit_text("📤 Converting...")
                            with open(mp3_path, 'rb') as audio_file:
                                await update.message.reply_audio(audio=audio_file)
                            await msg.edit_text("✅ Done!")
                            os.remove(latest_m4a)
                            os.remove(mp3_path)
                        else:
                            await msg.edit_text("❌ Conversion failed")
                    else:
                        await msg.edit_text("❌ No audio file created")
                        
        except Exception as e:
            logger.error(f"Download error: {e}")
            await msg.edit_text("❌ Download failed")
            
    except Exception as e:
        logger.error(f"General error: {e}")
        await update.message.reply_text("❌ Error")

def main():
    logger.info("🤖 Starting bot...")
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()
