FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY workers/piper_compat/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY workers/piper_compat/app.py /app/app.py

ENV PIPER_DATA_DIR=/models \
    PIPER_VOICE_NAME=ar_JO-kareem-medium \
    PIPER_SAMPLE_RATE=22050

EXPOSE 8001
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
