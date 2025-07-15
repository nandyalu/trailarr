Trailarr can be used with hardware acceleration to speed up video conversion using NVIDIA, Intel, and AMD GPUs. This guide explains how to set up Trailarr to leverage hardware acceleration from different GPU manufacturers.

!!! important
    Hardware acceleration is an advanced feature and requires additional setup on your host system. If you do not know/understand what hardware acceleration is, you can safely ignore this guide and use Trailarr without hardware acceleration.


!!! note
    Trailarr supports hardware acceleration using NVIDIA GPUs (CUDA), Intel GPUs (VAAPI), and AMD GPUs (AMF). The container automatically detects available GPU hardware during startup and uses the best acceleration method available.


## Prerequisites

Before you begin, ensure you have the following available based on your GPU type:

=== "NVIDIA GPU (CUDA)"
    - NVIDIA GPU
    - NVIDIA drivers installed on your system
    - NVIDIA Container Toolkit installed on your system

    If you haven't installed the NVIDIA Container Toolkit, follow the [official installation guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html){:target="_blank"}.

=== "Intel GPU (VAAPI)"
    - Intel GPU with hardware video acceleration support
    - Intel GPU drivers installed on your system
    - `/dev/dri` devices available to the container

=== "AMD GPU (AMF)"
    - AMD GPU with AMF (Advanced Media Framework) support
    - AMD GPU drivers installed on your system
    - `/dev/dri` devices available to the container


## Installation

To run Trailarr with hardware acceleration, you need to provide the appropriate runtime flags during installation based on your GPU type.

### NVIDIA GPUs

Run the following command to start Trailarr with NVIDIA GPU acceleration:

!!! important
    The important part of the command is the `runtime=nvidia` flag, which tells Docker to use the NVIDIA runtime. You can modify rest of the command to suit your needs.

=== "Docker Compose"

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
        runtime: nvidia  # <-- Add this line for NVIDIA GPUs
        volumes:
          - <LOCAL_APPDATA_FOLDER>:/config
          - <LOCAL_MEDIA_FOLDER>:<RADARR_ROOT_FOLDER>
          - <LOCAL_MEDIA_FOLDER>:<SONARR_ROOT_FOLDER>
        restart: on-failure
    ```

=== "Docker Run"

    ```bash
    docker run -d \
        --name=trailarr \
        -e TZ=America/New_York \
        -e PUID=1000 \
        -e PGID=1000 \
        -p 7889:7889 \
        --runtime=nvidia \  # <-- Add this line for NVIDIA GPUs
        -v <LOCAL_APPDATA_FOLDER>:/config \
        -v <LOCAL_MEDIA_FOLDER>:<RADARR_ROOT_FOLDER> \
        -v <LOCAL_MEDIA_FOLDER>:<SONARR_ROOT_FOLDER> \
        --restart unless-stopped \
        nandyalu/trailarr:latest
    ```

### Intel/AMD GPUs

Run the following command to start Trailarr with Intel or AMD GPU acceleration:

!!! important
    The important part of the command is the `device /dev/dri` flag, which gives the container access to the GPU hardware. You can modify rest of the command to suit your needs.

=== "Docker Compose"

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
        devices:
          - /dev/dri:/dev/dri  # <-- Add this line for Intel/AMD GPUs
        volumes:
          - <LOCAL_APPDATA_FOLDER>:/config
          - <LOCAL_MEDIA_FOLDER>:<RADARR_ROOT_FOLDER>
          - <LOCAL_MEDIA_FOLDER>:<SONARR_ROOT_FOLDER>
        restart: on-failure
    ```

=== "Docker Run"

    ```bash
    docker run -d \
        --name=trailarr \
        -e TZ=America/New_York \
        -e PUID=1000 \
        -e PGID=1000 \
        -p 7889:7889 \
        --device /dev/dri \  # <-- Add this line for Intel/AMD GPUs
        -v <LOCAL_APPDATA_FOLDER>:/config \
        -v <LOCAL_MEDIA_FOLDER>:<RADARR_ROOT_FOLDER> \
        -v <LOCAL_MEDIA_FOLDER>:<SONARR_ROOT_FOLDER> \
        --restart unless-stopped \
        nandyalu/trailarr:latest
    ```

## Testing Hardware Acceleration

Once you have set up Trailarr with hardware acceleration, you can test if it is working correctly:

=== "NVIDIA GPU (CUDA)"

    ```bash
    docker exec -it trailarr nvidia-smi
    ```

    If everything is set up correctly, you should see the NVIDIA GPU details in the output.

=== "Intel GPU (VAAPI)"

    ```bash
    docker exec -it trailarr ls -la /dev/dri
    ```

    If everything is set up correctly, you should see the DRI devices (like `renderD128`) in the output.

=== "AMD GPU (AMF)"

    ```bash
    docker exec -it trailarr ls -la /dev/dri
    ```

    If everything is set up correctly, you should see the DRI devices (like `renderD128`) in the output.

You can also check the GPU detection by looking at the container logs:
```bash
docker logs trailarr
```

Look for messages like "NVIDIA GPU is available", "Intel GPU detected", or "AMD GPU detected" in the startup logs.


### Enabling Hardware Acceleration in Trailarr

To enable hardware acceleration in Trailarr, navigate to `Settings` -> `General` -> `Advanced Settings` and enable the `Hardware Acceleration` option.

!!! note
    Trailarr automatically detects available GPU hardware and uses the best acceleration method available. The priority order is: NVIDIA > AMD > Intel > CPU fallback.

## Supported Codecs by GPU Type

=== "NVIDIA GPU (CUDA)"

    - **H.264** (`h264_nvenc`) - Full hardware acceleration
    - **H.265/HEVC** (`hevc_nvenc`) - Full hardware acceleration
    - **Other codecs** (VP8, VP9, AV1) - Software encoding (CPU fallback)

=== "Intel GPU (VAAPI)"

    - **H.264** (`h264_vaapi`) - Full hardware acceleration
    - **H.265/HEVC** (`hevc_vaapi`) - Full hardware acceleration
    - **Other codecs** (VP8, VP9, AV1) - Software encoding (CPU fallback)

=== "AMD GPU (AMF)"

    - **H.264** (`h264_amf`) - Full hardware acceleration
    - **H.265/HEVC** (`hevc_amf`) - Full hardware acceleration
    - **Other codecs** (VP8, VP9, AV1) - Software encoding (CPU fallback)

## When Hardware Acceleration is NOT Used

Hardware acceleration will automatically fall back to CPU encoding in the following cases:

1. **Unsupported Video Codecs**: VP8, VP9, and AV1 codecs are not supported by most GPU hardware encoders and will use CPU encoding
2. **Copy Video Format**: When the video format is set to "copy" in the trailer profile, no encoding occurs
3. **Hardware Acceleration Disabled**: When the "Hardware Acceleration" setting is disabled in Trailarr settings
4. **GPU Not Available**: When no compatible GPU is detected or accessible by the container
5. **Hardware Encoder Failure**: If the GPU encoder fails, the system automatically falls back to CPU encoding

## How Trailarr Uses Hardware Acceleration Internally

### Detection Process

1. **Container Startup**: During container startup, Trailarr automatically detects available GPU hardware
2. **NVIDIA Detection**: Uses `nvidia-smi` command to detect NVIDIA GPUs
3. **Intel/AMD Detection**: Checks for `/dev/dri` devices and uses `lspci` to identify Intel/AMD GPUs
4. **Environment Variables**: Sets `NVIDIA_GPU_AVAILABLE`, `INTEL_GPU_AVAILABLE`, and `AMD_GPU_AVAILABLE` environment variables

### Acceleration Priority

When multiple GPUs are available, Trailarr uses the following priority order:

1. **NVIDIA GPU** (highest priority) - Uses CUDA hardware acceleration
2. **AMD GPU** - Uses AMF hardware acceleration
3. **Intel GPU** - Uses VAAPI hardware acceleration  
4. **CPU Fallback** (lowest priority) - Uses software encoding

### Command Examples

=== "NVIDIA GPU (CUDA)"

    ```bash
    ffmpeg \
        -hwaccel cuda \
        -hwaccel_output_format cuda \
        -i input.mkv \
        -c:v h264_nvenc \
        -preset fast \
        -cq 22 \
        -c:a aac \
        -b:a 128k \
        output.mkv
    ```

=== "Intel GPU (VAAPI)"

    ```bash
    ffmpeg \
        -init_hw_device vaapi=intel \
        -filter_hw_device intel \
        -i input.mkv \
        -vf format=nv12,hwupload \
        -c:v h264_vaapi \
        -crf 22 \
        -async_depth 4 \
        -c:a aac \
        -b:a 128k \
        output.mkv
    ```

=== "AMD GPU (AMF)"

    ```bash
    ffmpeg \
        -i input.mkv \
        -c:v h264_amf \
        -crf 22 \
        -preset balanced \
        -quality balanced \
        -usage transcoding \
        -c:a aac \
        -b:a 128k \
        output.mkv
    ```

## Helpful Links

- [NVIDIA Container Toolkit Installation Guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html){:target="_blank"}
- [Docker Compose - GPU](https://docs.docker.com/compose/how-tos/gpu-support/){:target="_blank"}
- [Docker GPU Support](https://docs.docker.com/desktop/features/gpu/){:target="_blank"}
- [Enable NVIDIA in WSL](https://learn.microsoft.com/en-us/windows/ai/directml/gpu-cuda-in-wsl){:target="_blank"}
- [NVIDIA Blog Post](https://developer.nvidia.com/blog/gpu-containers-runtime/){:target="_blank"}
- [Intel VAAPI Documentation](https://github.com/intel/libva){:target="_blank"}
- [AMD AMF Documentation](https://github.com/GPUOpen-LibrariesAndSDKs/AMF){:target="_blank"}
- [FFmpeg Hardware Acceleration](https://trac.ffmpeg.org/wiki/HWAccelIntro){:target="_blank"}