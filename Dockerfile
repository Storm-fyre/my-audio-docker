# Dockerfile
FROM python:3.9-slim

# Install ffmpeg (and any other needed packages) in one RUN step:
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Set a working directory inside the container
WORKDIR /app

# Copy requirements and install them
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app code
COPY . .

# The default command to run when the container starts:
#   Render provides a PORT environment variable, so we bind to 0.0.0.0:$PORT
CMD gunicorn app:app --bind 0.0.0.0:$PORT