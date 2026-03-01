import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8631686831:AAFvy57We-AfDOIAwbdTsyIyjOE7immc4Is"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send YouTube URL")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if not ('youtube.com' in text or 'youtu.be' in text):
        await update.message.reply_text("Send YouTube URL")
        return
    
    try:
        msg = await update.message.reply_text("Downloading...")
        
        # Use yt-dlp directly via command line (more reliable)
        output_file = "/tmp/downloaded_audio.mp3"
        
        result = subprocess.run([
            'yt-dlp', '-x', '--audio-format', 'mp3', 
            '-o', output_file, text
        ], capture_output=True, text=True)
        
        logger.info(f"yt-dlp return code: {result.returncode}")
        logger.info(f"yt-dlp stdout: {result.stdout}")
        logger.info(f"yt-dlp stderr: {result.stderr}")
        
        if result.returncode == 0 and os.path.exists(output_file):
            with open(output_file, 'rb') as f:
                await update.message.reply_audio(audio=f)
            await msg.edit_text("Done!")
            os.remove(output_file)
        else:
            await msg.edit_text(f"Failed: {result.stderr[:100]}")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("Error")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()
