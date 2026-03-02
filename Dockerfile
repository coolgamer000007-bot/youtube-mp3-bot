# ---- Base image -------------------------------------------------
FROM python:3.9-slim               # Python 3.9 – works with PTB 13.x

# ---- Install system packages (ffmpeg is needed for MP3 conversion)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# ---- Working directory -----------------------------------------
WORKDIR /app

# ---- Install Python dependencies ---------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy the bot code -----------------------------------------
COPY . .

# ---- Run the bot ------------------------------------------------
CMD ["python", "youtube_bot.py"]
