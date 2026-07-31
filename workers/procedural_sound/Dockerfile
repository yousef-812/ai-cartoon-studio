FROM python:3.11-slim

WORKDIR /app
COPY workers/procedural_sound/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY workers/procedural_sound/app.py /app/app.py

ENV SOUND_SAMPLE_RATE=48000
EXPOSE 8002
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8002"]
