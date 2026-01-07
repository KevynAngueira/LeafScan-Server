FROM python:3.11-slim

# Working directory
WORKDIR /app

# System dependencies (OpenCV, ffmpeg, etc.)
RUN apt-get update && apt-get install -y \
    git ffmpeg libgl1 libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

# Clone the server repo (Flask + Dockerfile)
RUN git clone --depth 1 --branch main https://github.com/KevynAngueira/LeafScan-Server.git /app/LeafScan-Server

# Clone LeafScan package (library)
RUN git clone --depth 1 --branch main-revamped https://github.com/KevynAngueira/LeafScan.git /app/LeafScan

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/LeafScan-Server/requirements.txt
RUN pip install --no-cache-dir -r /app/LeafScan/requirements.txt

# Install LeafScan package itself
RUN pip install -e /app/LeafScan

# Add both repos to PYTHONPATH (optional if -e works)
ENV PYTHONPATH="/app/LeafScan-Server:/app/LeafScan:$PYTHONPATH"

# Expose Flask port
EXPOSE 5000

# Start the Flask server
CMD ["python", "/app/LeafScan-Server/app.py"]

