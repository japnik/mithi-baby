# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install system dependencies (FFMPEG, ImageMagick)
# FFMPEG is required for video generation
# ImageMagick is required for some MoviePy operations (TextClip)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    fonts-liberation \
    fonts-noto \
    fonts-lohit-deva \
    fonts-lohit-guru \
    && rm -rf /var/lib/apt/lists/*

# Fix ImageMagick policy to allow text rendering (common MoviePy issue)
RUN if [ -f /etc/ImageMagick-6/policy.xml ]; then sed -i 's/none/read,write/g' /etc/ImageMagick-6/policy.xml; elif [ -f /etc/ImageMagick-7/policy.xml ]; then sed -i 's/none/read,write/g' /etc/ImageMagick-7/policy.xml; fi

# Set the working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY backend/requirements.txt ./backend/requirements.txt

# Install python dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy the entire project
COPY . .

# Final check: set permissions for frontend
RUN chmod -R 755 /app/frontend

# Environment variables
# PYTHONUNBUFFERED=1 ensures logs show up in Cloud Logging
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose the port
EXPOSE 8080

# Run the server
CMD ["python", "backend/server.py"]
