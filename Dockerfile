FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    git ffmpeg libgl1 libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

# Clone repos
RUN git clone --depth 1 --branch main https://github.com/KevynAngueira/LeafScan-Server.git /app/LeafScan-Server
RUN git clone --depth 1 --branch main-revamped https://github.com/KevynAngueira/LeafScan.git /app/LeafScan

# Install dependencies
RUN pip install --no-cache-dir -r /app/LeafScan-Server/requirements.txt
RUN pip install --no-cache-dir -r /app/LeafScan/requirements.txt

# Install LeafScan as a package
RUN pip install -e /app/LeafScan

# VERY IMPORTANT: include LeafScanApp in PYTHONPATH
ENV PYTHONPATH="/app/LeafScan-Server/LeafScanApp:/app/LeafScan:$PYTHONPATH"

# Set working directory to the old Flask app
WORKDIR /app/LeafScan-Server/LeafScanApp

# Expose Flask port
EXPOSE 5000

# Run the OLD Flask server
CMD ["python", "App.py"]
