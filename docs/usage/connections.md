## Add Radarr/Sonarr Connections

1. Navigate to the application in your browser at [http://localhost:7889/settings/connections](http://localhost:7889/settings/connections){:target="_blank"}.

    !!! info "Trailarr Login"
        When you open Trailarr in browser, it will ask you to login. Default login is:
        
        ```bash
        Username: admin
        Password: trailarr
        ```

2. Go to `Settings` > `Connections` and Click the `Add New` button to add your Radarr and Sonarr instances.
![Add New](../getting-started/add-new.png)

3. Add your Radarr and Sonarr instances.
![Add Connection](add-connection.png)

4. Set the `Connection Name` to a name of your choice.

5. Set the `Type` to either `Radarr` or `Sonarr`.

6. Set the `Monitor Type` to your preference. See [Monitor Types](#monitor-types) below for more information.

    !!! tip
        _You can set different monitor types for each Radarr/Sonarr instance._


7. Add the `URL` for your Radarr or Sonarr instance.
    Full URL of your Radarr or Sonarr instance including the port number. For example, `http://192.168.0.15:6969`.

8. Add the `API Key` from your Radarr or Sonarr instance.
    Get `API Key` by opening Radarr/Sonarr in your browser, going to `Settings > General`, then copy the API key.

9. If you have a setup that requires `Path Mappings` to be set as described in [Volume Mapping](../getting-started/volume-mapping.md), you can add them here. See [Path Mapping](#path-mapping) below for more information.

    If you need additional help, there is a [Docker Config Tool](https://nandyalu.github.io/trailarr/usage/docker-builder.html){:target="_blank"} that will help you generate the docker-compose file with the correct volume mappings and path mappings.

    !!! tip
        _You can set different path mappings for each Radarr/Sonarr instance._

    !!! warning
        _Path mappings are optional and only required if you have a setup that requires them._

10. Click the `Save` button to save the connection.

11. Repeat the steps for each Radarr and Sonarr instance you want to monitor.

12. That's it! The application will now start downloading trailers for your media library. See [settings](../getting-started/application-settings.md) for more information on how to adjust settings.

## Monitor Types

### `Missing`
Monitors and downloads trailers for movies/series without a trailer.

### `New`
Only Monitors and download trailers for movies/series that gets added after the change.

### `Sync`
Monitors and downloads trailers for movie/series that are monitored in Radarr/Sonarr.

### `None`
Turns off monitoring for the connection and does not download any trailers.

!!! tip
    _If you have a huge library and don't want to download trailers for all of them, set the monitor type to `None` when adding a Radarr/Sonarr Connection. Wait for an hour or so to let the app sync all media from that connection, and change it to `New` to download trailers for new media. You can always manually set the monitor type for the movies/series you want to download trailers for._

## Path Mapping

In simple words, Path Mappings are used to tell Trailarr what to replace the path with when it gets a path from Radarr/Sonarr. `Path From` is what it looks for in the path, and `Path To` is what it replaces it with.

If you are using Windows, you might need to add path mappings in most cases, unless you are also running Radarr/Sonarr as docker containers. See [Volume Mapping](../install/volume-mapping.md) for more information.

!!! info
    Path mappings are optional and only required if you have a setup that requires them. You can set different path mappings for each Radarr/Sonarr instance.

??? example
    Adding a path mapping for a connection as:
    ```yaml
    Path From: C:\Users\username\Movies
    Path To: /media/movies
    ```
    will replace `C:\Users\username\Movies` with `/media/movies` in the path received from Radarr/Sonarr.
    So, if Radarr/Sonarr sends a path like `C:\Users\username\Movies\The MAtrix (1999)`, it will be replaced with `/media/movies/The Matrix (1999)`.

1. Click the `Add Path Mapping` button.
![Add Path Mapping](../getting-started/add-path-mapping.png)

2. Set the `Path From` to the path inside Radarr/Sonarr connection.

3. Set the `Path To` to the path inside the Trailarr container.
![Path Mapping](../getting-started/path-mapping.png)

4. Click the `Save` button to save the path mapping.

5. Repeat the steps for each path mapping you want to add, if needed.

!!! tip
    _Path mappings are useful when the media folder available to Radarr/Sonarr is same for multiple connections. For example, if Radarr has media folder set to `/media` and Sonarr has media folder set to `/media`, you can map the local folder for Radarr media to `/media/movies` and Sonarr media to `/media/tv` and then in add path mappings with `Path From` set to `/media` and `Path To` set to `/media/movies` for Radarr and `/media/tv` for Sonarr connections._

!!! warning
    For Path Mappings to work, you need to set the `Path From` to the exact path inside Radarr/Sonarr connection and `Path To` to the exact path inside the Trailarr container. If the paths do not match, the path mapping will not work. Path Mappings needs to be paired with `Volume Mapping` in the `docker-compose.yml` file. See [Volume Mapping](../install/volume-mapping.md) for more information.