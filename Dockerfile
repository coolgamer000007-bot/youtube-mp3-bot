FROM python:3.11-slim

WORKDIR /app

# Install FFmpeg properly
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    ffmpeg -version

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "youtube_bot.py"]
