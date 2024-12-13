FROM mcr.microsoft.com/devcontainers/python:1-3.12-bullseye
# Install the xz-utils package
RUN apt-get update && apt-get install -y curl xz-utils tzdata git gnupg2

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - &&\
    apt-get install -y nodejs

# Install specific version of npm
RUN npm install -g npm@10.9.1

# Install specific version of Angular CLI
RUN npm install -g @angular/cli@19.0.1

# Install Python Packages
COPY dev-requirements.txt .
RUN python -m pip install --no-cache-dir --upgrade -r dev-requirements.txt

# Download and extract the custom FFmpeg build from yt-dlp
RUN curl -L -o /tmp/ffmpeg.tar.xz "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz" \
    && mkdir /tmp/ffmpeg \
    && tar -xf /tmp/ffmpeg.tar.xz -C /tmp/ffmpeg --strip-components=1 \
    && mv /tmp/ffmpeg/bin/* /usr/local/bin/ \
    && rm -rf /tmp/ffmpeg.tar.xz /tmp/ffmpeg

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ="America/New_York" \
    APP_NAME="Trailarr" \
    APP_VERSION="0.2.1-beta"

# Set the python path
ENV PYTHONPATH "${PYTHONPATH}:/app/backend"

# Copy startup script
COPY dev-start.sh /usr/local/bin/startup.sh
RUN chmod +x /usr/local/bin/startup.sh

# For GPG signing
RUN echo 'export GPG_TTY=$(tty)' >> /root/.bashrc
RUN echo 'export GPG_TTY=$(tty)' >> /home/vscode/.bashrc
RUN echo 'gpg-connect-agent updatestartuptty /bye >/dev/null' >> /root/.bashrc
RUN echo 'gpg-connect-agent updatestartuptty /bye >/dev/null' >> /home/vscode/.bashrc

# Expose the port the app runs on
EXPOSE 7888
