# Stage 1 - Build Angular app
FROM node:20.12.2 AS build

# Install specific version of npm
RUN npm install -g npm@10.7.0

# Install specific version of Angular CLI
RUN npm install -g @angular/cli@17.3.6

# Copy your frontend
COPY ./frontend /app/frontend
WORKDIR /app/frontend

# Install dependencies
RUN npm install

# Build Angular app
RUN ng build

# Run bash command to check if the build is successful
# Start a process that runs indefinitely
# CMD ["tail", "-f", "/dev/null"]

# Stage 2 - Python dependencies
FROM python:3.12-slim AS python-deps

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY ./backend/requirements.txt .
RUN python -m pip install --no-cache-dir --upgrade -r requirements.txt

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Stage 3 - Final image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create a directory for the app
RUN mkdir /app

# Create data folder for storing database and other config files
# RUN mkdir -p /data/logs && chmod -R 755 /data

# Set the working directory
WORKDIR /app

# Copy the frontend build from the previous stage
COPY --from=build /app/frontend/dist/frontend/browser /app/frontend

# Copy the backend
COPY ./backend /app/backend

# Copy the installed Python dependencies
COPY --from=python-deps /usr/local/ /usr/local/

# Set the python path
ENV PYTHONPATH "${PYTHONPATH}:/app/backend"

# Expose the port the app runs on
EXPOSE 7889

# Copy start.sh script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Run startup script
# CMD ["gunicorn", "--bind", "0.0.0.0:7889", "-k", "uvicorn.workers.UvicornWorker", "backend.main:trailarr_api"]
CMD ["/bin/sh", "/app/start.sh"]
# CMD ["tail", "-f", "/dev/null"]