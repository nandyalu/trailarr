Trailarr can be used with hardware acceleration to speed up video conversion using NVIDIA, Intel, and AMD GPUs. This guide explains how to set up Trailarr to leverage hardware acceleration from different GPU manufacturers.

!!! important
    Hardware acceleration is an advanced feature and requires additional setup on your host system. If you do not know/understand what hardware acceleration is, you can safely ignore this guide and use Trailarr without hardware acceleration.


!!! note
    Trailarr supports hardware acceleration using NVIDIA GPUs (CUDA) and Intel/AMD GPUs (VAAPI). The container automatically detects available GPU hardware during startup and uses the best acceleration method available (configurable in `Settings > General`).

!!! info "Runtime Libraries Included"
    The Trailarr container includes the necessary runtime libraries and ffmpeg build with hardware acceleration support:
    
    - **Intel/AMD GPU**: `libva2`, `libva-drm2`, `intel-media-va-driver`, `i965-va-driver`, `mesa-va-drivers`, `vainfo`
    - **NVIDIA GPU**: Uses NVIDIA Container Toolkit (runtime provided by host)
    
    The container uses static FFMPEG builds from [yt-dlp/FFmpeg-Builds](https://github.com/yt-dlp/FFmpeg-Builds){:target="_blank"} with comprehensive hardware acceleration support.


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
    - Host user (your self user account) added to `render` and/or `video` groups (optional, but recommended)

    ??? example "Drivers installation and GPU access"

        You can install the necessary Intel Drivers and add access to GPU device with below commands. This is a basic example, steps for your particular system and hardware might vary. Please refer to offical documentation.
        
        ```bash
        # Ubuntu/Debian - Install Intel GPU drivers and VAAPI support
        sudo apt update
        sudo apt install intel-media-va-driver i965-va-driver vainfo
        
        # Add your user to render and video groups
        sudo usermod -a -G render,video $USER
        
        # Verify VAAPI functionality
        vainfo
        ```

    The Trailarr container includes the necessary Intel GPU runtime libraries. Ensure your Intel GPU drivers support VAAPI acceleration.

=== "AMD GPU (VAAPI)"
    - AMD GPU with VAAPI support (most modern AMD GPUs)
    - AMD GPU drivers installed on your system
    - `/dev/dri` devices available to the container
    - Host user (your self user account) added to `render` and/or `video` groups (optional, but recommended)
    
    ??? example "Drivers installation and GPU access"

        You can install the necessary AMD (Mesa) Drivers and add access to GPU device with below commands. This is a basic example, steps for your particular system and hardware might vary. Please refer to offical documentation.

        ```bash
        # Ubuntu/Debian - Install AMD GPU drivers and VAAPI support
        sudo apt update
        sudo apt install mesa-va-drivers vainfo
        
        # Add your user to render and video groups
        sudo usermod -a -G render,video $USER
        
        # Verify VAAPI functionality
        vainfo
        ```

    The Trailarr container includes the necessary AMD GPU runtime libraries. AMD GPUs use VAAPI through Mesa drivers for hardware acceleration.


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
        devices:  # <-- Add this line for Intel/AMD GPUs
          - /dev/dri:/dev/dri  # <-- And this line
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

??? note "Multiple GPUs on your system"

    If you have multiple GPUs, you can just pass the actual device that you want to use with Trailarr. 
    
    For example, if you have an Intel UHD Graphics (CPU integrated Graphics) and a dedicated Intel ARC GPU, then you will have `/dev/dri/renderD128` (Intel UHD) and `/dev/dri/renderD129` (Intel ARC) and you want to use the Intel ARC with Trailarr, then use this

    ```yaml
        # rest of the docker-compose
        devices:
          - /dev/dri/renderD129:/dev/dri/renderD129
    ```

## Testing Hardware Acceleration

Once you have set up Trailarr with hardware acceleration, you can test if it is working correctly:

=== "NVIDIA GPU (CUDA)"

    ```bash
    docker exec -it trailarr nvidia-smi
    ```

    If everything is set up correctly, you should see the NVIDIA GPU details in the output.

=== "Intel/AMD GPU (VAAPI)"

    ```bash
    docker exec -it trailarr ls -la /dev/dri
    ```

    If everything is set up correctly, you should see the DRI devices (like `renderD128`) in the output.
    
    Test VAAPI functionality:
    ```bash
    docker exec -it trailarr vainfo --display drm --device /dev/dri/renderD128
    ```
    
    This should show the available VAAPI profiles supported by your GPU.

You can also check the GPU detection by looking at the container logs:
```bash
docker logs trailarr
```

Look for messages like "NVIDIA GPU detected", "Intel GPU detected", or "AMD GPU detected" in the startup logs. The logs will also show detailed GPU information and VAAPI capabilities when available.

## Host System Setup

Trailarr takes care of most of these automatically during startup so you don't have to. However, there are some situations where Trailarr might not be able to do so and you can try the below to try and make it work.

### User Group Configuration (Intel/AMD GPUs)

For optimal Intel/AMD GPU performance, ensure your host user is added to the appropriate groups:

```bash
# Add current user to render and video groups
sudo usermod -a -G render,video $USER

# Verify group membership (log out and back in if needed)
groups
```

### Permissions and Device Access

The container needs access to `/dev/dri` devices for hardware acceleration:

```bash
# Check DRI device permissions on host
ls -la /dev/dri/

# Should show something like:
# crw-rw---- 1 root render 226, 128 ... renderD128
# crw-rw---- 1 root video  226, 0   ... card0
```

If you encounter permission issues, you may need to run the container with specific user/group IDs:

```yaml
# Docker Compose - matching host user
services:
  trailarr:
    image: nandyalu/trailarr:latest
    environment:
      - PUID=${UID}
      - PGID=${GID}
    # ... rest of config
```

!!! info "Automatic Group Assignment"
    The Trailarr container automatically attempts to add the container user (`appuser`) to the necessary GPU groups (`render`, `video`, and common GPU group IDs like 226, 128, 129) during startup. This reduces the need for manual group configuration in most cases.


### Enabling Hardware Acceleration in Trailarr

To enable hardware acceleration in Trailarr, navigate to `Settings` -> `General` -> `Advanced Settings` and enable the `Hardware Acceleration` option.

!!! note
    Trailarr automatically detects available GPU hardware and uses the best acceleration method available (if multiple methods are detected and enabled). The priority order is: NVIDIA > Intel VAAPI > AMD VAAPI > CPU fallback.

## Supported Codecs by GPU Type

=== "NVIDIA GPU (CUDA)"

    - **H.264** (`h264_nvenc`) - Full hardware acceleration
    - **H.265/HEVC** (`hevc_nvenc`) - Full hardware acceleration
    - **AV1** (`av1_nvenc`) - Full hardware acceleration
    - **Other codecs** (VP8, VP9) - Harware acceleration NOT supported, CPU fallback for Software encoding

=== "Intel/AMD GPU (VAAPI)"

    - **H.264** (`h264_vaapi`) - Full hardware acceleration
    - **H.265/HEVC** (`hevc_vaapi`) - Full hardware acceleration
    - **VP8** (`vp8_vaapi`) - Full hardware acceleration
    - **VP9** (`vp9_vaapi`) - Full hardware acceleration
    - **AV1** (`av1_vaapi`) - Full hardware acceleration

!!! note "Unified VAAPI Approach"
    Both Intel and AMD GPUs use VAAPI (Video Acceleration API) for hardware acceleration. This simplifies the implementation and provides consistent performance across different GPU manufacturers.

## When Hardware Acceleration is NOT Used

Hardware acceleration will automatically fall back to CPU encoding in the following cases:

1. **Unsupported Video Codecs**: VP8, VP9, and AV1 codecs are not supported by older GPU hardware encoders and will use CPU encoding
2. **Copy Video Format**: When the video format is set to "copy" in the trailer profile, no encoding occurs
3. **Hardware Acceleration Disabled**: When the "Hardware Acceleration" setting is disabled in Trailarr settings
4. **GPU Not Available**: When no compatible GPU is detected or accessible by the container
5. **Hardware Encoder Failure**: If the GPU encoder fails, the system automatically falls back to CPU encoding

## How Trailarr Uses Hardware Acceleration Internally

### Detection Process

1. **Container Startup**: During container startup, Trailarr automatically detects available GPU hardware
2. **NVIDIA Detection**: Uses `nvidia-smi` command to detect NVIDIA GPUs
3. **Intel/AMD Detection**: Checks for `/dev/dri` devices and uses `lspci` to identify Intel/AMD GPUs
4. **Dynamic Device Mapping**: Automatically maps specific GPU devices (e.g., `/dev/dri/renderD128`, `/dev/dri/renderD129`) to Intel/AMD GPUs
5. **Environment Variables**: Sets `GPU_AVAILABLE_NVIDIA`, `GPU_AVAILABLE_INTEL`, `GPU_AVAILABLE_AMD`, and device-specific paths

### Acceleration Priority

When multiple GPUs are available, Trailarr uses the following priority order:

1. **NVIDIA GPU** (highest priority) - Uses CUDA hardware acceleration
2. **Intel/AMD GPU** - Uses VAAPI hardware acceleration  
3. **CPU Fallback** (lowest priority) - Uses software encoding

### Command Examples

=== "NVIDIA GPU (CUDA)"

    ```bash
    ffmpeg \
        -hwaccel cuda \
        -hwaccel_output_format cuda \
        -i input.mkv \
        -vf scale_cuda=format=nv12 \
        -c:v h264_nvenc \
        -preset fast \
        -cq 22 \
        -b:v 0 \
        -pix_fmt yuv420p \
        -c:a aac \
        -b:a 128k \
        output.mkv
    ```

=== "Intel/AMD GPU (VAAPI)"

    ```bash
    ffmpeg \
        -hwaccel vaapi \
        -hwaccel_device [dynamic_device_path] \  # e.g., /dev/dri/renderD128
        -vaapi_device [dynamic_device_path] \  # e.g., /dev/dri/renderD128
        -i input.mkv \
        -vf format=nv12,hwupload \
        -c:v h264_vaapi \
        -qp 22 \
        -b:v 0 \
        -pix_fmt yuv420p \
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
- [Intel Media Drivers](https://github.com/intel/media-driver/){:target="_blank"}
- [AMD AMF Documentation](https://github.com/GPUOpen-LibrariesAndSDKs/AMF){:target="_blank"}
- [FFmpeg Hardware Acceleration](https://trac.ffmpeg.org/wiki/HWAccelIntro){:target="_blank"}
- [Jellyfin Hardware Acceleration](https://jellyfin.org/docs/general/post-install/transcoding/hardware-acceleration/){:target="_blank"}
