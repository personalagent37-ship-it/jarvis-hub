# Use official Python lightweight base image
FROM python:3.10-slim

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies, Node.js 20, Chromium, and X11/headless browser libraries
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    build-essential \
    python3-dev \
    linux-libc-dev \
    libxss1 \
    libasound2 \
    libgtk-3-0 \
    libgbm-dev \
    libnss3 \
    libgl1 \
    libglib2.0-0 \
    xvfb \
    xauth \
    xfonts-base \
    x11-xkb-utils \
    procps \
    psmisc \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for Chromium, Puppeteer, and Headless X11 Display
ENV DISPLAY=:99
ENV XDG_RUNTIME_DIR=/tmp
ENV BROWSER_ENGINE=chromium
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy Python requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install-deps chromium 2>/dev/null || true

# Copy Node.js hub requirements and install packages without strict lockfile checks
COPY jarvis_hub/package*.json ./jarvis_hub/
RUN cd jarvis_hub && npm install --no-package-lock --no-audit && npx puppeteer browsers install chrome

# Copy the entire JARVIS repository into the container
COPY . .

# Expose port 5000 (Python Brain Webhook) and 3000 (Node.js Hub)
EXPOSE 5000 3000

# Clean stale X11 lock files, start Xvfb virtual screen directly, wait 3s for display socket, and launch Python Brain & Node.js WhatsApp Gateway
CMD ["/bin/bash", "-c", "rm -rf /tmp/.X* /tmp/.X11-unix && Xvfb :99 -screen 0 1280x1024x24 -ac +extension GLX +render -noreset & sleep 3 && python3 whatsapp_server.py & cd jarvis_hub && node hub.js"]
