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
            }],
            'outtmpl': '/tmp/%(title)s.%(ext)s',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(text, download=True)
            filename = ydl.prepare_filename(info)
            mp3_filename = filename.replace('.webm', '.mp3')
            
            if os.path.exists(mp3_filename):
                with open(mp3_filename, 'rb') as audio_file:
                    await update.message.reply_audio(audio=audio_file)
                
                await msg.edit_text("Done!")
                os.remove(mp3_filename)
                
    except Exception as e:
        await update.message.reply_text("Error")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()
