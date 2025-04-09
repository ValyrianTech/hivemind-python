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
COPY requirements.txt ./requirements.txt
COPY ../requirements.txt ./project-requirements.txt

# Install dependencies using --system flag
RUN uv pip install --system -r requirements.txt -r project-requirements.txt

# Install the hivemind-python package from PyPI
RUN uv pip install --system hivemind-python

## ------------------------------- IPFS Stage ------------------------------ ##
FROM ipfs/kubo:latest AS ipfs

## ------------------------------- Production Stage ------------------------------ ##
FROM python:3.10-slim-bookworm AS production

# Install dependencies for IPFS
RUN apt-get update && apt-get install --no-install-recommends -y \
        curl supervisor && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Create a user for the application
RUN useradd --create-home appuser

# Copy IPFS binary from IPFS stage
COPY --from=ipfs /usr/local/bin/ipfs /usr/local/bin/ipfs

# Set up IPFS directories with correct permissions
RUN mkdir -p /home/appuser/.ipfs && \
    chown -R appuser:appuser /home/appuser/.ipfs

# Initialize IPFS with the appuser
USER appuser
RUN ipfs init && \
    ipfs config Addresses.API /ip4/0.0.0.0/tcp/5001 && \
    ipfs config Addresses.Gateway /ip4/0.0.0.0/tcp/8080
USER root

# Create supervisor configuration
RUN mkdir -p /etc/supervisor/conf.d
# Copy supervisord configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create log directory for supervisor
RUN mkdir -p /var/log/supervisor

# Create app directory with proper permissions
RUN mkdir -p /app && chown -R appuser:appuser /app

# Copy application files
COPY app.py /app/
COPY websocket_handlers.py /app/
COPY templates /app/templates
COPY static /app/static

# Create proper directory structure for the hivemind package
USER root
RUN mkdir -p /app/src/hivemind

# Copy the hivemind package from the local filesystem
# Note: This assumes the build script is run from the root directory
COPY ../src /app/src

# Copy the entire project structure for the web app
COPY .. /app/hivemind-python

# Set proper permissions for the application directories
RUN chown -R appuser:appuser /app

# Switch to appuser for application setup
USER appuser
WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/logs /app/data

# Create a symlink to make the hivemind module accessible
RUN ln -sf /app/src/hivemind /app/hivemind

# Set up the correct Python path for the hivemind module
ENV PYTHONPATH="/app:/app/src:${PYTHONPATH}"

# Copy dependencies from builder stage
COPY --from=builder --chown=appuser:appuser /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

# Expose ports for FastAPI and IPFS
EXPOSE 8000 5001 8080

# Switch back to root to run supervisor
USER root

# Start supervisor which will manage both IPFS and the hivemind app
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
