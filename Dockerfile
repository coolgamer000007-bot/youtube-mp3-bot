# ---- Base image -------------------------------------------------
FROM python:3.9-slim          # Python 3.9 – fully supported by PTB v13

# ---- OS packages ------------------------------------------------
# ffmpeg is required only if you ever convert to MP3.
# (You can omit the apt‑get line if you want to keep the file as .m4a)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# ---- Working directory -------------------------------------------
WORKDIR /app

# ---- Python dependencies -----------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Application code -------------------------------------------
COPY . .

# ---- Start the bot ------------------------------------------------
CMD ["python", "youtube_bot.py"]
