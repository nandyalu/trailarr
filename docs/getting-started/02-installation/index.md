# Installation

<!-- md:version:upd 0.9.0 -->

Trailarr can be installed using Docker (recommended) or directly on your system for advanced use cases.

We have guides for installing Trailarr using these methods:

- [Docker Compose](./docker-compose.md) ⭐ **Recommended**
- [Docker Run](./docker-run.md)
- [Direct Install](./baremetal.md) - For advanced users
- [Build and Install](./self-install.md) - For developers / custom environments
- [Unraid](./unraid.md)

!!! tip "Hardware Acceleration"
    Trailarr also supports Hardware Acceleration using Intel, AMD, and NVIDIA GPUs for converting downloaded trailers. Direct installations provide better GPU access, especially in virtualized environments like Proxmox LXC. See details in [Hardware Acceleration](./hardware-acceleration.md) section.

## Which Installation Method to Choose?

### Docker (Recommended)
- **Best for**: Most users, easy setup and updates
- **Pros**: Simple installation, isolated environment, easy updates
- **Cons**: Container overhead, complex GPU passthrough in some environments

### Direct Install
- **Best for**: Advanced users, GPU acceleration in LXC, performance-critical deployments
- **Pros**: Direct hardware access, better performance, native GPU support
- **Cons**: More complex setup, manual updates, less isolation

### Build and Install
- **Best for**: Developers, custom environments, non-standard setups
- **Pros**: Full control over each step, works in any environment
- **Cons**: Most complex setup, fully manual process

### Installation Method Comparison

| Feature | Docker | Direct Install | Build and Install |
|---------|--------|----------------|-------------------|
| Setup Difficulty | Easy | Moderate | Advanced |
| Update Process | Simple | `trailarr update` | Manual |
| Resource Usage | Higher | Lower | Lower |
| Hardware Access | Limited | Full | Full |
| GPU in LXC | Complex | Native | Native |
| Isolation | Complete | Process-level | Process-level |

Each method has its own set of instructions, so choose the one that best fits your setup.

It is recommended to use Docker Compose for most installations, as it simplifies the process of managing containers and configurations. Choose direct installation if you need direct hardware access or are running in environments where Docker GPU passthrough is problematic (such as Proxmox LXC containers). Use build and install if the installer script doesn't work in your environment or you want full manual control.

!!! tip
    There are some things you need to know for installing Trailarr, which are explained in [Docker Compose](./docker-compose.md) section. Please read that section before proceeding with the installation.