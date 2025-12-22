# 1. Set base image
FROM python:3.13-slim

# 2. Set environment variables
# PATH: Add the virtual environment's bin directory to the system's PATH.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# 3. Create virtual environment and install dependencies
WORKDIR /app

# Create a virtual environment
RUN python3 -m venv /opt/venv

# Copy requirements.txt first to leverage Docker's layer caching
COPY requirements.txt .

# Upgrade pip and install dependencies without caching to optimize image size
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 4. Copy application code and run
COPY . .

# Expose the application port
EXPOSE $PORT

# Run the server
CMD ["python", "server.py"]