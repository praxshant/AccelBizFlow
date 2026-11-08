FROM python:3.11-slim

WORKDIR /app

# System deps for OpenCV and EasyOCR
RUN apt-get update && apt-get install -y \
    libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install EasyOCR
RUN pip install --no-cache-dir easyocr

COPY . .

ENV JWT_SECRET="change-in-production"
ENV PYTHONPATH="/app"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
