## ------------------------------- Builder Stage ------------------------------ ## 
FROM python:3.10-bookworm AS builder

RUN apt-get update && apt-get install --no-install-recommends -y \
        build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Download the latest installer, install it and then remove it
ADD https://astral.sh/uv/install.sh /install.sh
RUN chmod -R 655 /install.sh && /install.sh && rm /install.sh

# Set up the UV environment path correctly
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

# Copy the requirements files
COPY ./hivemind/requirements.txt ./requirements.txt
COPY ./requirements.txt ./project-requirements.txt

# Install dependencies using --system flag
RUN uv pip install --system -r requirements.txt -r project-requirements.txt

## ------------------------------- IPFS Stage ------------------------------ ##
FROM ipfs/kubo:latest AS ipfs

## ------------------------------- Production Stage ------------------------------ ##
FROM python:3.10-slim-bookworm AS production

# Install dependencies for IPFS
RUN apt-get update && apt-get install --no-install-recommends -y \
        curl supervisor && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy IPFS binary from IPFS stage
COPY --from=ipfs /usr/local/bin/ipfs /usr/local/bin/ipfs

# Set up IPFS directories
RUN mkdir -p /data/ipfs && \
    ipfs init && \
    ipfs config Addresses.API /ip4/0.0.0.0/tcp/5001 && \
    ipfs config Addresses.Gateway /ip4/0.0.0.0/tcp/8080

# Create a user for the application
RUN useradd --create-home appuser
# Give ownership of IPFS data to appuser
RUN chown -R appuser:appuser /data/ipfs

# Create supervisor configuration
RUN mkdir -p /etc/supervisor/conf.d
COPY --chown=root:root <<EOF /etc/supervisor/conf.d/supervisord.conf
[supervisord]
nodaemon=true
user=root
logfile=/var/log/supervisor/supervisord.log
logfile_maxbytes=50MB
logfile_backups=10

[program:ipfs]
command=ipfs daemon
user=appuser
autostart=true
autorestart=true
stdout_logfile=/var/log/supervisor/ipfs.log
stderr_logfile=/var/log/supervisor/ipfs-error.log

[program:hivemind]
command=python -m uvicorn app:app --host 0.0.0.0 --port 8000
directory=/app
user=appuser
autostart=true
autorestart=true
stdout_logfile=/var/log/supervisor/hivemind.log
stderr_logfile=/var/log/supervisor/hivemind-error.log
EOF

# Create log directory for supervisor
RUN mkdir -p /var/log/supervisor

# Switch to appuser for application setup
USER appuser

WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/logs /app/data

# Copy application files
COPY --chown=appuser:appuser ./hivemind/app.py ./
COPY --chown=appuser:appuser ./hivemind/websocket_handlers.py ./
COPY --chown=appuser:appuser ./hivemind/templates ./templates
COPY --chown=appuser:appuser ./hivemind/static ./static

# Copy the entire project structure to maintain the correct imports
COPY --chown=appuser:appuser . /app/hivemind-python
# Create a symlink to make the hivemind module accessible
RUN ln -s /app/hivemind-python/src/hivemind /app/hivemind

# Copy dependencies from builder stage
COPY --from=builder --chown=appuser:appuser /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

# Add the project directory to PYTHONPATH
ENV PYTHONPATH="/app:/app/hivemind-python:${PYTHONPATH}"

# Expose ports for FastAPI and IPFS
EXPOSE 8000 5001 8080

# Switch back to root to run supervisor
USER root

# Start supervisor which will manage both IPFS and the hivemind app
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
