FROM python:3.11-slim

# Tesseract aur poppler install karo (system software)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# App ka code copy karo
WORKDIR /app
COPY . /app

# Python libraries install karo
RUN pip install --no-cache-dir -r requirements.txt

# Server chalao
CMD uvicorn app:app --host 0.0.0.0 --port $PORT