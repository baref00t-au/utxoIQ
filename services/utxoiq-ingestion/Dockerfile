# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies including Tor
RUN apt-get update && apt-get install -y \
    gcc \
    tor \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Copy tor configuration and startup script
COPY torrc ./torrc
COPY start.sh ./start.sh
RUN chmod +x start.sh

# Expose port
EXPOSE 8080

# Run startup script (handles Tor + service)
CMD ["./start.sh"]
