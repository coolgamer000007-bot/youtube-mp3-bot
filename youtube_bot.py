import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

logging.basicConfig(level=logging.INFO)
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
        msg = await update.message.reply_text("Downloading...")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': '/tmp/%(title)s.%(ext)s',
            'extractaudio': True,  # Force audio extraction
            'audioformat': 'mp3',  # Force MP3 format
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(text, download=True)
            
            # Get the actual downloaded file path
            actual_filename = ydl.prepare_filename(info)
            
            # Find the actual MP3 file (it might have different extension)
            mp3_filename = None
            for ext in ['.mp3', '.m4a', '.webm']:
                potential_file = actual_filename.replace('.webm', '.mp3').replace('.m4a', '.mp3')
                if os.path.exists(potential_file):
                    mp3_filename = potential_file
                    break
            
            # If no file found, try the actual filename
            if not mp3_filename and os.path.exists(actual_filename):
                mp3_filename = actual_filename
            
            if mp3_filename and os.path.exists(mp3_filename):
                # Ensure it has .mp3 extension for Telegram
                final_filename = mp3_filename
                if not mp3_filename.endswith('.mp3'):
                    final_filename = mp3_filename + '.mp3'
                    os.rename(mp3_filename, final_filename)
                
                # Send the file
                with open(final_filename, 'rb') as audio_file:
                    await update.message.reply_audio(
                        audio=audio_file,
                        filename=os.path.basename(final_filename)
                    )
                
                await msg.edit_text("Done!")
                
                # Clean up
                if os.path.exists(final_filename):
                    os.remove(final_filename)
                    
            else:
                await msg.edit_text("Download failed - file not found")
                
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("Error occurred")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()
