FROM python:3.11-slim

WORKDIR /app

# System dependencies + Redis
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    git ffmpeg libgl1 libglib2.0-0 \
    redis-server redis-tools \
 && rm -rf /var/lib/apt/lists/*

# Configure Redis to listen only locally
RUN sed -i 's/^bind .*/bind 127.0.0.1/' /etc/redis/redis.conf \
 && sed -i 's/^protected-mode .*/protected-mode yes/' /etc/redis/redis.conf \
 && sed -i 's/^daemonize .*/daemonize no/' /etc/redis/redis.conf

# Clone repos
RUN git clone --depth 1 --branch main https://github.com/KevynAngueira/LeafScan-Server.git /app/LeafScan-Server
RUN git clone --depth 1 --branch main-revamped https://github.com/KevynAngueira/LeafScan.git /app/LeafScan

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/LeafScan-Server/requirements.txt
RUN pip install --no-cache-dir -r /app/LeafScan/requirements.txt
RUN pip install -e /app/LeafScan

# Python path
ENV PYTHONPATH="/app/LeafScan-Server/LeafScanApp:/app/LeafScan:$PYTHONPATH"

WORKDIR /app/LeafScan-Server/LeafScanApp

EXPOSE 5000

# Start Redis in background, then Flask
CMD redis-server /etc/redis/redis.conf & python App.py
