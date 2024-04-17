# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.12-slim

EXPOSE 7889

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Install pip requirements
COPY ./backend/requirements.txt .
RUN python -m pip install --no-cache-dir --upgrade -r requirements.txt

# TODO: Update below to use /backend folder for fastapi
# Refer to https://fastapi.tiangolo.com/deployment/docker/ for RESTAPI deployment
WORKDIR /code
COPY ./backend /code/backend

# Copy config
COPY ./configs /code/configs

# Copy Frontend files
COPY ./frontend /code/frontend

# Create logs folder
RUN mkdir /code/logs

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /code
USER appuser

# Run Migrations to create/update the database
RUN alembic upgrade head

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["gunicorn", "--bind", "0.0.0.0:7889", "-k", "uvicorn.workers.UvicornWorker", "backend.main:trailarr_api"]
# TODO: Update the CMD to also include the frontend
