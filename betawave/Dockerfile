# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 
    PYTHONDONTWRITEBYTECODE=1

# Set work directory
WORKDIR /app

# Install system dependencies including ffmpeg
RUN apt-get update && 
    apt-get install -y --no-install-recommends 
    ffmpeg 
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create the data directory
RUN mkdir -p data

# Expose the port the app runs on
EXPOSE 8501

# Command to run the application
CMD ["python", "app.py"]
