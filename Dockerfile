# ---- Base image -------------------------------------------------
FROM python:3.9-slim

# ---- Install system packages (ffmpeg needed for optional MP3 conversion) ----
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# ---- Working directory -----------------------------------------
WORKDIR /app

# ---- Install Python dependencies ---------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy bot source code ---------------------------------------
COPY . .

# ---- Command to run the bot -------------------------------------
CMD ["python", "youtube_bot.py"]
