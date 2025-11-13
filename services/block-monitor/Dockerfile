# Use Python 3.12 slim image
FROM python:3.12-slim

# Install tor and required packages
RUN apt-get update && apt-get install -y \
    tor \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY block-monitor.py .

# Copy tor configuration
COPY torrc /etc/tor/torrc

# Create startup script
COPY start.sh .
RUN chmod +x start.sh

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose port for health checks
EXPOSE 8080

# Run startup script (starts tor and monitor)
CMD ["./start.sh"]
