# ---- Base image -------------------------------------------------
FROM python:3.9-slim

# ---- Install ffmpeg (needed for MP3 conversion) ---------------
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# ---- Working directory -----------------------------------------
WORKDIR /app

# ---- Install Python dependencies ---------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy the bot source code ----------------------------------
COPY . .

# ---- Run the bot ------------------------------------------------
CMD ["python", "youtube_bot.py"]
