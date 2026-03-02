# ---- Base image -------------------------------------------------
FROM python:3.9-slim

# ---- Install OS packages ---------------------------------------
# ffmpeg is required for audio conversion (keeps the file as MP3)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# ---- Working directory -----------------------------------------
WORKDIR /app

# ---- Python dependencies ----------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Application code -------------------------------------------
COPY . .

# ---- Start the bot ----------------------------------------------
CMD ["python", "youtube_bot.py"]
