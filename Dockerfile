FROM python:3.11-slim

WORKDIR /app

# Copy requirements first (Docker layer caching optimization)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Use entrypoint script
ENTRYPOINT ["./entrypoint.sh"]