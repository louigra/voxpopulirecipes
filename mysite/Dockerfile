# Use a lightweight Python image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies (including Tesseract OCR)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files
COPY . .

# Expose the port (important for Railway)
EXPOSE 8000

# Start the Django application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "mysite.wsgi:application"]