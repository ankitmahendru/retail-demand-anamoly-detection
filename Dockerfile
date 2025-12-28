# Use a lightweight Python 3.9 image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Install necessary system packages
# gcc is often needed for compiling Python C-extensions (like numpy/pandas)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code into the container
COPY src/ ./src/

# Create directories for persistent data
RUN mkdir -p data models logs

# Expose the port Flask runs on
EXPOSE 5000

# Set Python path so 'src' module can be found
ENV PYTHONPATH=/app

# Healthcheck to ensure the service is running
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:5000/health')"

# Run the Flask application module
CMD ["python", "-m", "src.app"]