FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p indexes

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose ports for FastAPI and Streamlit
EXPOSE 8000 8501

# Create a script to run both services
RUN echo '#!/bin/bash\n\
uvicorn backend.app:app --host 0.0.0.0 --port 8000 & \n\
streamlit run frontend/app.py --server.port=8501 --server.address=0.0.0.0 --server.enableCORS=false\n\
wait\n' > /app/start.sh && chmod +x /app/start.sh

# Start both services
CMD ["/app/start.sh"]