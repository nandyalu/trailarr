# Installation

This guide will walk you through installing Trailarr using Docker. You can use either Docker Compose (recommended for most users) or a `docker run` command.

Before you begin, make sure you have reviewed the "First Things" section to understand environment variables and how to find your existing Radarr/Sonarr volume mappings.

## Using Docker Compose

Create a `docker-compose.yml` file with the following content. Adjust the volumes and environment variables to match your setup.

```yaml
version: "3.8"
services:
  trailarr:
    image: ghcr.io/trailarr/trailarr:latest # Or specify a version tag
    container_name: trailarr
    environment:
      - TZ=Your/Timezone # e.g., America/New_York
      - TR_APP_DIR=/appdata # Path inside the container for Trailarr's data
      # Add any other environment variables as needed.
      # Refer to the [Environment Variables](../getting-started/environment-variables.md) documentation.
    volumes:
      - /path/to/your/trailarr/appdata:/appdata # For Trailarr's database and logs
      # Map your Radarr media folder(s)
      - /path/on/your/host/movies:/movies # Example: if Radarr uses /movies internally
      # Map your Sonarr media folder(s)
      - /path/on/your/host/tv:/tv # Example: if Sonarr uses /tv internally
      # Add more volume mappings if you have multiple Radarr/Sonarr instances
      # or if your media is split across different locations.
      # The path on the right (e.g., /movies, /tv) is how Trailarr will see these folders.
      # The path on the left is the actual path on your Docker host system.
    ports:
      - "3699:3699" # Or choose a different host port if 3699 is taken
    restart: unless-stopped
    # Optional: Add healthcheck, labels, network configuration as needed
```

**Explanation of important parts:**

*   `image`: Specifies the Trailarr Docker image. It's good practice to pin to a specific version in production.
*   `container_name`: A friendly name for your container.
*   `environment`:
    *   `TZ`: Set your timezone.
    *   `TR_APP_DIR`: Specifies where Trailarr stores its configuration and database *inside the container*. The corresponding host path is defined in `volumes`.
*   `volumes`:
    *   `/path/to/your/trailarr/appdata:/appdata`: This is crucial. It maps a directory on your host machine (e.g., `/opt/trailarr/config` or `/home/user/docker/trailarr/appdata`) to `/appdata` inside the Trailarr container. This is where Trailarr will store its persistent data. **Replace `/path/to/your/trailarr/appdata` with an actual path on your system.**
    *   `/path/on/your/host/movies:/movies` and `/path/on/your/host/tv:/tv`: These are examples. You **must** update these.
        *   The left side (`/path/on/your/host/...`) should be the **same host path** that your Radarr/Sonarr containers use for their media.
        *   The right side (`:/movies`, `:/tv`) is how this path will be known *inside the Trailarr container*. You will use these paths later when configuring connections in Trailarr.
*   `ports`:
    *   `"3699:3699"`: Maps port 3699 on your host to port 3699 in the container. If port 3699 is already in use on your host, you can change the left side (e.g., `"3700:3699"`).
*   `restart: unless-stopped`: Ensures the container restarts automatically unless you explicitly stop it.

Once you have customized your `docker-compose.yml` file, save it and run:
```bash
docker-compose up -d
```
To update Trailarr later, you can run:
```bash
docker-compose pull trailarr
docker-compose up -d
```

## Using `docker run`

If you prefer not to use Docker Compose, you can use the `docker run` command. Be sure to replace placeholders with your actual paths and settings.

```bash
docker run -d \
  --name trailarr \
  -e TZ="Your/Timezone" \
  -e TR_APP_DIR="/appdata" \
  # Add any other environment variables as needed
  -p 3699:3699 \
  -v /path/to/your/trailarr/appdata:/appdata \
  -v /path/on/your/host/movies:/movies \
  -v /path/on/your/host/tv:/tv \
  # Add more volume mappings as needed
  --restart unless-stopped \
  ghcr.io/trailarr/trailarr:latest # Or specify a version tag
```

**Explanation of important parts:**

*   `-d`: Runs the container in detached mode (in the background).
*   `--name trailarr`: Assigns a name to the container.
*   `-e TZ="Your/Timezone"`: Sets your timezone.
*   `-e TR_APP_DIR="/appdata"`: Specifies Trailarr's internal application data directory.
*   `-p 3699:3699`: Maps port 3699 on your host to port 3699 in the container. Change the host port (left side) if needed.
*   `-v /path/to/your/trailarr/appdata:/appdata`: **Crucial for persistent data.** Replace `/path/to/your/trailarr/appdata` with an actual path on your host system.
*   `-v /path/on/your/host/movies:/movies`: **Map your media folders.** Replace `/path/on/your/host/movies` with the actual path on your host system that Radarr uses. The `:/movies` part is how Trailarr will see this folder. Repeat for Sonarr and other media locations.
*   `--restart unless-stopped`: Ensures the container restarts automatically.
*   `ghcr.io/trailarr/trailarr:latest`: The Docker image to use.

Choose the method that best suits your Docker management style. Once installed, you can proceed to the Configuration steps.
