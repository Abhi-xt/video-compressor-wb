FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy your app
COPY . /app

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Start the app using gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000"]
