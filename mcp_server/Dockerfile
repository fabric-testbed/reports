# Production Multi-Stage Dockerfile for FABRIC Reports MCP Server
#
# Features:
# - Multi-stage build for smaller image size
# - Non-root user for security
# - Optimized layer caching
# - Health check
# - Production-ready configuration
#
# For local/stdio development, see Dockerfile.local

# ============================================================================
# Stage 1: Builder
# ============================================================================
FROM python:3.11-slim AS builder

LABEL maintainer="Komal Thareja <komal.thareja@gmail.com>"
LABEL stage="builder"

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv

# Activate virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install dependencies
WORKDIR /build
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================================================
# Stage 2: Runtime
# ============================================================================
FROM python:3.11-slim

LABEL maintainer="Komal Thareja <komal.thareja@gmail.com>"
LABEL description="FABRIC Reports MCP Server - Production Build"
LABEL version="1.4.0"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create non-root user
RUN useradd -m -u 10001 -s /bin/bash appuser && \
    mkdir -p /var/log/mcp && \
    chown -R appuser:appuser /var/log/mcp

# Set working directory
WORKDIR /app

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    MCP_ENV=prod \
    REPORTS_API_BASE_URL="http://reports-api:8080/reports" \
    PORT=5000 \
    MCP_TRANSPORT__MODE="http" \
    MCP_LOGGING__LEVEL="INFO" \
    MCP_LOGGING__FORMAT="json" \
    MCP_LOGGING__DESTINATION="both" \
    MCP_LOGGING__FILE_PATH="/var/log/mcp/server.log"

# Copy application code
COPY --chown=appuser:appuser . /app/

# Switch to non-root user
USER appuser

# Expose ports
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run application
CMD ["python", "/app/mcp_reports_server.py"]
