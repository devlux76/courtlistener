FROM python:3.13-slim

# Install system dependencies, PostgreSQL client, and Chromium dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget \
        gnupg \
        ca-certificates \
        jq \
        unzip \
        curl \
        gcc \
        libpq-dev \
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

# Copy requirements and install all Python dependencies
COPY docker/bulk-data/requirements.txt /workspace/requirements.txt
RUN pip install --no-cache-dir -r /workspace/requirements.txt

# Copy fetch and import scripts, and shell entrypoints
COPY ../../scripts/fetch_bulk_data.py /workspace/fetch_bulk_data.py
COPY ../../scripts/import_bulk_data.py /workspace/import_bulk_data.py
COPY ../../scripts/fetch_bulk_data.sh /workspace/fetch_bulk_data.sh
COPY ../../scripts/import_bulk_data.sh /workspace/import_bulk_data.sh

# Add entrypoint scripts for fetch and import
COPY docker/bulk-data/entrypoint-fetch.sh /workspace/entrypoint-fetch.sh
COPY docker/bulk-data/entrypoint-import.sh /workspace/entrypoint-import.sh
RUN chmod +x /workspace/entrypoint-fetch.sh /workspace/entrypoint-import.sh /workspace/fetch_bulk_data.sh /workspace/import_bulk_data.sh

# Add a non-root user for security
RUN useradd -ms /bin/bash bulkuser
USER bulkuser

WORKDIR /workspace

# Environment variables for PostgreSQL connection (can be overridden at runtime)
ENV BULK_DB_HOST=localhost
ENV BULK_DB_USER=postgres
ENV BULK_DB_PASSWORD=postgres
ENV BULK_DB_NAME=courtlistener

# Default entrypoint (can be overridden with --entrypoint)
ENTRYPOINT ["/bin/bash"]