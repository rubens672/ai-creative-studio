# Use the official Python base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies (including graphviz for agent workflow visualization)
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Setup directory structure for ADK agent discovery: /app/agents/<agent_name>/
WORKDIR /app/agents/multi_content_creation

# Copy pyproject.toml first for efficient Docker layer caching
COPY pyproject.toml .

# Install dependencies into virtual environment
RUN uv sync --no-install-project --no-dev

# Copy agent application code
COPY . .

# Set working directory to /app
WORKDIR /app

# Create a non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV HOST=0.0.0.0
ENV PATH="/app/agents/multi_content_creation/.venv/bin:$PATH"

# Expose port for Cloud Run
EXPOSE 8080

# Launch ADK Web UI
CMD ["adk", "web", "--host", "0.0.0.0", "--port", "8080", "--allow_origins=*", "/app/agents"]
