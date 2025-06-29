Before you begin, make sure you have reviewed the [First Things](../01-first-things/index.md) section to understand environment variables and how to find your existing Radarr/Sonarr volume mappings.

!!! tip "Use Docker Compose"
    It is recommended to use `Docker Compose`, as it makes it easy to update to latest version and/or update the configuration later if needed

If you prefer not to use Docker Compose, you can use the `docker run` command. Be sure to replace placeholders with your actual paths and settings.

```bash
docker run -d \
  --name trailarr \
  -e TZ="America/New_York" \
  # Add any other environment variables as needed
  -p 7889:7889 \
  -v /path/to/your/trailarr:/config \
  -v /path/on/your/host/movies:/movies \
  -v /path/on/your/host/tv:/tv \
  # Add more volume mappings as needed
  --restart unless-stopped \
  nandyalu/trailarr:latest
```

## **Explanation of options:**

For a detailed explanation of how to setup each of these see [Docker Compose](./docker-compose.md).

*   `-d`: Runs the container in detached mode (in the background).
*   `--name trailarr`: Assigns a name to the container.
*   `-e OPTION=VALUE`: An environment variable to use with the container.
*   `-p 7889:7889`: Maps port 7889 on your host to port 7889 in the container. Change the host port (left side) if needed.
*   `-v HOST_PATH:CONTAINER_PATH`: Map a HOST_PATH (path in your computer/server) to an INTERNAL_PATH (path inside Trailarr container).
*   `--restart unless-stopped`: Ensures the container restarts automatically when unhealthy.
*   `nandyalu/trailarr:latest`: The Docker image to use.

Now that Trailarr is up and running, we need to configure it to connect to our `Radarr` and `Sonarr` to let it start doing it's job - download trailers. We will go over that in the next section [Setup](../03-setup/index.md).
