FROM python:3.13-slim

# Install system dependencies and Chromium dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget \
        gnupg \
        ca-certificates \
        jq \
        unzip \
        curl \
        fonts-liberation \
        libasound2 \
        libatk-bridge2.0-0 \
        libatk1.0-0 \
        libc6 \
        libcairo2 \
        libcups2 \
        libdbus-1-3 \
        libdrm2 \
        libexpat1 \
        libgbm1 \
        libglib2.0-0 \
        libgtk-3-0 \
        libnspr4 \
        libnss3 \
        libpango-1.0-0 \
        libx11-6 \
        libx11-xcb1 \
        libxcb1 \
        libxcomposite1 \
        libxcursor1 \
        libxdamage1 \
        libxext6 \
        libxfixes3 \
        libxi6 \
        libxrandr2 \
        libxrender1 \
        libxss1 \
        libxtst6 \
        chromium \
        chromium-driver && \
    ln -sf /usr/lib/chromium/chromedriver /usr/bin/chromedriver && \
    rm -rf /var/lib/apt/lists/*

# Install selenium and requests
RUN pip install selenium requests

# Add a non-root user for security
RUN useradd -ms /bin/bash bulkuser
USER bulkuser

WORKDIR /workspace

ENTRYPOINT ["/bin/bash"]