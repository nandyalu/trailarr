# --------------------------------------------------------------------------- #
#                      Stage 1 - Frontend Build (Node.js)                     #
# --------------------------------------------------------------------------- #
FROM node:24-slim AS frontend-build

WORKDIR /app/frontend

# Copy package files for dependency installation
COPY ./frontend/package*.json ./
COPY ./frontend/contract ./contract
COPY ./frontend/ng-openapi-gen.json ./

# Install dependencies
RUN npm ci

# Copy frontend source files
COPY ./frontend/ ./

# Build the frontend for production
RUN npm run build

# --------------------------------------------------------------------------- #
#                          Stage 2 - Final image                              #
# --------------------------------------------------------------------------- #
FROM nandyalu/python-ffmpeg:latest

# python3.13, uv, gosu, yt-dlp, deno (for yt-dlp-ejs), ffmpeg with hw acceleration drivers are pre-installed

# Set the working directory
WORKDIR /app

# Copy uv related files from backend for dependency installation
COPY ./backend/.python-version /app/backend/.python-version
COPY ./backend/pyproject.toml /app/backend/pyproject.toml
COPY ./backend/uv.lock /app/backend/uv.lock

# Install Python dependencies using uv pip install
WORKDIR /app/backend
RUN uv pip install --no-cache --native-tls --system -r pyproject.toml

# ARG APP_VERSION, will be set during build by github actions
ARG APP_VERSION=0.6.1-dev

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ="America/New_York" \
    APP_NAME="Trailarr" \
    APP_MODE="Docker" \
    APP_PORT=7889 \
    APP_DATA_DIR="/config" \
    PUID=1000 \
    PGID=1000 \
    APP_VERSION=${APP_VERSION} \
    NVIDIA_VISIBLE_DEVICES="all" \
    NVIDIA_DRIVER_CAPABILITIES="all"


# Set the working directory
WORKDIR /app

# Copy the assets folder
COPY ./assets /app/assets

# Copy the backend
COPY ./backend /app/backend

# Copy the frontend built files from the frontend-build stage
COPY --from=frontend-build /app/frontend-build /app/frontend-build

# Set the python path
ENV PYTHONPATH=/app/backend

# Copy the scripts folder, and make all scripts executable (including subdirectories)
COPY ./scripts /app/scripts
RUN find /app/scripts -name "*.sh" -type f -exec chmod +x {} \;

# Expose the port the app runs on
EXPOSE ${APP_PORT}

# Set permissions for appuser on /app directory
RUN chmod -R 750 /app

# Define a healthcheck command
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=10s \
    CMD python /app/scripts/healthcheck.py ${APP_PORT}

# Run entrypoint script to create directories, set permissions and timezone \
# and start the application as appuser
ENTRYPOINT ["/app/scripts/entrypoint.sh"]
