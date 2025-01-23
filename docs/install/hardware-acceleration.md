Trailarr can be used with hardware acceleration to speed up video conversion using NVIDIA GPUs. This guide explains how to set up Trailarr to leverage hardware acceleration from NVIDIA GPUs.

!!! important
    Hardware acceleration is an advanced feature and requires additional setup on your host system. If you do not know/understand what hardware acceleration is, you can safely ignore this guide and use Trailarr without hardware acceleration.


!!! warning
    Trailarr only supports hardware acceleration using NVIDIA GPUs at this time. Intel and AMD GPUs are not supported.


## Prerequisites

Before you begin, ensure you have the following available:

- NVIDIA GPU
- NVIDIA drivers installed on your system
- NVIDIA Container Toolkit installed on your system

If you haven't installed the NVIDIA Container Toolkit, follow the [official installation guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html){:target="_blank"}.


## Installation

To run Trailarr with hardware acceleration, you need to provide nvidia runtime flags during installation. 

### Docker CLI

Run the following command to start Trailarr with hardware acceleration:

!!! important
    The important part of the command is the `--runtime=nvidia` flag, which tells Docker to use the NVIDIA runtime. You can modify rest of the command to suit your needs.

```bash
docker run -d \
    --name=trailarr \
    -e TZ=America/New_York \
    -e PUID=1000 \
    -e PGID=1000 \
    -p 7889:7889 \
    --runtime=nvidia \  # <-- Add this line
    -v <LOCAL_APPDATA_FOLDER>:/config \
    -v <LOCAL_MEDIA_FOLDER>:<RADARR_ROOT_FOLDER> \
    -v <LOCAL_MEDIA_FOLDER>:<SONARR_ROOT_FOLDER> \
    --restart unless-stopped \
    nandyalu/trailarr:latest
```

### Docker Compose

If you are using Docker Compose, you can add the `runtime: nvidia` flag to the service definition:

```yaml
services:
    trailarr:
        image: nandyalu/trailarr:latest
        container_name: trailarr
        environment:
            - TZ=America/New_York
            - PUID=1000
            - PGID=1000
        ports:
            - 7889:7889
        runtime: nvidia  # <-- Add this line
        volumes:
            - <LOCAL_APPDATA_FOLDER>:/config
            - <LOCAL_MEDIA_FOLDER>:<RADARR_ROOT_FOLDER>
            - <LOCAL_MEDIA_FOLDER>:<SONARR_ROOT_FOLDER>
        restart: on-failure
```

### Testing Hardware Acceleration

Once you have set up Trailarr with hardware acceleration, you can test if it is working correctly by running the following command:

```bash
docker exec -it trailarr nvidia-smi
```

If everything is set up correctly, you should see the NVIDIA GPU details in the output.


### Enabling Hardware Acceleration in Trailarr

To enable hardware acceleration in Trailarr, navigate to `Settings` -> `General` -> `Advanced Settings` and enable the `Hardware Acceleration` option.

!!! note
    Hardware acceleration with NVIDIA GPUs is only available for `H.264` and `H.265` codecs at this time. Other codecs use software encoding.