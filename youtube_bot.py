import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp
import random
import time

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
        msg = await update.message.reply_text("🔍 Preparing download...")
        
        # Configuration that bypasses restrictions
        ydl_opts = {
            # Use a common audio format that works
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': '/tmp/%(title)s.%(ext)s',
            
            # Bypass restrictions
            'ignoreerrors': True,
            'nooverwrites': True,
            'retries': 3,
            'fragment_retries': 3,
            'skip_unavailable_fragments': True,
            
            # Simulate browser behavior
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate',
            },
            
            # Audio extraction settings
            'extractaudio': True,
            'audioformat': 'mp3',
            'audioquality': '192',
            
            # Progress and logging
            'quiet': False,
            'no_warnings': False,
        }
        
        # Add random delay to avoid detection
        await asyncio.sleep(random.uniform(1, 3))
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Get video info first
                info = ydl.extract_info(text, download=False)
                if not info:
                    await msg.edit_text("❌ Cannot access video info")
                    return
                
                title = info.get('title', 'Unknown')
                logger.info(f"Video accessible: {title}")
                
                await msg.edit_text(f"⬇️ Downloading: {title[:40]}...")
                
                # Download with retry logic
                success = False
                for attempt in range(2):
                    try:
                        ydl.download([text])
                        success = True
                        break
                    except Exception as e:
                        logger.warning(f"Attempt {attempt+1} failed: {e}")
                        if attempt < 1:  # Only retry once
                            await msg.edit_text(f"🔄 Retrying... ({attempt+1}/2)")
                            await asyncio.sleep(2)
                
                if not success:
                    await msg.edit_text("❌ Download failed after retries")
                    return
                
                # Find the downloaded file
                expected_file = ydl.prepare_filename(info)
                logger.info(f"Expected file: {expected_file}")
                
                # Check various possible file locations
                files_to_check = [
                    expected_file,
                    expected_file.replace('.webm', '.mp3'),
                    expected_file.replace('.m4a', '.mp3'),
                    expected_file.replace('.webm', '.m4a'),
                ]
                
                found_file = None
                for file_path in files_to_check:
                    if os.path.exists(file_path):
                        found_file = file_path
                        file_size = os.path.getsize(file_path)
                        logger.info(f"Found file: {found_file} ({file_size} bytes)")
                        break
                
                if found_file and os.path.getsize(found_file) > 1000:
                    await msg.edit_text("📤 Sending audio...")
                    
                    # Send whatever format we got
                    with open(found_file, 'rb') as audio_file:
                        await update.message.reply_audio(
                            audio=audio_file,
                            title=title[:64],
                            performer="YouTube Audio"
                        )
                    
                    await msg.edit_text("✅ Audio sent!")
                    os.remove(found_file)
                else:
                    await msg.edit_text("❌ No valid audio file created")
                        
        except Exception as e:
            logger.error(f"Download processing error: {e}")
            # Try one more alternative method
            await try_direct_download(update, msg, text)
            
    except Exception as e:
        logger.error(f"General error: {e}")
        await update.message.reply_text("❌ Processing failed")

async def try_direct_download(update: Update, msg, url):
    """Direct command-line yt-dlp approach"""
    try:
        await msg.edit_text("🔄 Trying direct method...")
        
        # Use yt-dlp command line directly
        output_file = "/tmp/direct_output.%(ext)s"
        cmd = [
            'yt-dlp',
            '-x',  # Extract audio
            '--audio-format', 'mp3',
            '--audio-quality', '192',
            '-o', output_file,
            '--ignore-errors',
            url
        ]
        
        import subprocess
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        logger.info(f"Direct method return: {result.returncode}")
        logger.info(f"Direct method stdout: {result.stdout}")
        logger.info(f"Direct method stderr: {result.stderr}")
        
        # Find the output file
        for ext in ['mp3', 'm4a', 'webm']:
            file_path = f"/tmp/direct_output.{ext}"
            if os.path.exists(file_path) and os.path.getsize(file_path) > 1000:
                await msg.edit_text("📤 Sending file...")
                with open(file_path, 'rb') as f:
                    await update.message.reply_audio(audio=f)
                await msg.edit_text("✅ Success!")
                os.remove(file_path)
                return
        
        await msg.edit_text("❌ Direct method failed")
        
    except Exception as e:
        logger.error(f"Direct method error: {e}")
        await msg.edit_text("❌ All methods failed")

def main():
    logger.info("🚀 Starting YouTube MP3 Bot...")
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()
