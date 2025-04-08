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

## ------------------------------- Production Stage ------------------------------ ##
FROM python:3.10-slim-bookworm AS production

RUN useradd --create-home appuser
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

# Expose the port for FastAPI
EXPOSE 8000

# Start the application with Uvicorn
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
