# Use the official Python base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies + Node.js (required for notion-mcp-server)
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g @notionhq/notion-mcp-server@1.9.1

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy pyproject.toml first for better layer caching
COPY pyproject.toml .

# Install Python dependencies
RUN uv sync --no-install-project --no-dev

# Copy application code
COPY . .

# Create a non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV HOST=0.0.0.0

ENV NOTION_TOKEN=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
ENV NOTION_PROJECT_DATABASE_ID=51d1425a7f32447d8fc35aaabcfda342
ENV NOTION_TASKS_DATABASE_ID=603d4d4bcb674bf0816e77c289a30ad6

# Expose the port Cloud Run will use
EXPOSE 8080

# Run the A2A server
CMD ["uv", "run", "python", "agent.py"]