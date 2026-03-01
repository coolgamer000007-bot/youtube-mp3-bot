import os
import re
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import yt_dlp

# --------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ----- put YOUR BOT TOKEN HERE --------------------------------
BOT_TOKEN = "8631686831:AAFvy57We-AfDOIAwbdTsyIyjOE7immc4Is"

# --------------------------------------------------------------
def start(update: Update, context: CallbackContext) -> None:
    """Send a small welcome + a one‑button keyboard."""
    btn = KeyboardButton(text="🟢 Send YouTube URL")
    markup = ReplyKeyboardMarkup([[btn]], resize_keyboard=True, one_time_keyboard=True)
    update.message.reply_text(
        "🎧 Welcome! Press the button (or just type) and send a YouTube link.\n"
        "The bot will return the audio as an MP3.",
        reply_markup=markup,
    )

# --------------------------------------------------------------
def clean_url(url: str) -> str:
    """Remove tracking parameters (e.g. ?si=…) that some links contain."""
    return re.sub(r"\?.*$", "", url.strip())

# --------------------------------------------------------------
def download_audio(url: str) -> str | None:
    """
    Use yt‑dlp to fetch the best audio stream and store it as an MP3.
    Returns the full path to the created file, or None on failure.
    """
    opts = {
        "format": "bestaudio/best",
        "outtmpl": "/tmp/%(title)s.%(ext)s",
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
        ],
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # yt‑dlp returns the *final* filename after post‑processing
            file_path = ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".m4a", ".mp3")
            return file_path if os.path.isfile(file_path) else None
    except Exception as e:
        logger.error(f"yt‑dlp failed: {e}")
        return None

# --------------------------------------------------------------
def handle_message(update: Update, context: CallbackContext) -> None:
    """Main handler – receives the URL, downloads, sends the MP3."""
    raw_text = update.message.text
    if not raw_text:
        return

    url = clean_url(raw_text)

    # Basic validation – we only accept YouTube links
    if not ("youtube.com" in url or "youtu.be" in url):
        update.message.reply_text("❌ Please send a valid YouTube URL.")
        return

    msg = update.message.reply_text("⏳ Downloading…")

    mp3_path = download_audio(url)

    if not mp3_path:
        msg.edit_text("❌ Download failed – the video may be restricted or offline.")
        return

    # Send the file
    try:
        with open(mp3_path, "rb") as f:
            update.message.reply_audio(
                audio=f,
                title=os.path.splitext(os.path.basename(mp3_path))[0],
                caption="✅ Here’s your MP3!",
            )
        msg.edit_text("✅ Done!")
    finally:
        # Clean‑up the temporary file (always)
        if os.path.exists(mp3_path):
            os.remove(mp3_path)

# --------------------------------------------------------------
def main() -> None:
    """Start the bot."""
    logger.info("🚀 Starting YouTube‑MP3 bot…")
    updater = Updater(BOT_TOKEN, use_context=True)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Polling (Railway will keep the container alive)
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
