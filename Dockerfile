# ---- Base image -------------------------------------------------
FROM python:3.9-slim

# ---- Install OS packages ---------------------------------------
# ffmpeg is required for audio conversion to MP3
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# ---- Working directory -----------------------------------------
WORKDIR /app

# ---- Python dependencies ----------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy application code --------------------------------------
COPY . .

# ---- Command to run the bot ------------------------------------
CMD ["python", "youtube_bot.py"]
