# ---- Base image -------------------------------------------------
FROM python:3.9-slim      # Python 3.9 – fully supported by PTB v13

# ---- Install OS packages ---------------------------------------
# ffmpeg is needed for audio conversion (optional if you only send the raw file)
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
