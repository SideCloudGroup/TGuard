# Multi-stage build for smaller final image
FROM python:3.13-alpine AS builder

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    postgresql-dev

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.13-alpine

# Install only runtime dependencies
RUN apk add --no-cache \
    libpq \
    && adduser -D -s /bin/sh app

WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/app/.local

# Copy application code (includes static files)
COPY . .

USER app

# Add user's local bin to PATH
ENV PATH=/home/app/.local/bin:$PATH

EXPOSE 8000

# Default command (will be overridden in docker-compose)
CMD ["python", "-m", "src.api.main"]
