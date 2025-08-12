# Installation

Trailarr can be installed using Docker (recommended) or directly on bare metal for advanced use cases.

We have guides for installing Trailarr using these methods:

- [Docker Compose](./docker-compose.md) ⭐ **Recommended**
- [Docker Run](./docker-run.md)
- [Bare Metal](./baremetal.md) - For advanced users
- [Unraid](./unraid.md)

!!! tip "Hardware Acceleration
    Trailarr also supports Hardware Acceleration using Intel, AMD, and NVIDIA GPUs for converting downloaded trailers. Bare metal installations provide better GPU access, especially in virtualized environments like Proxmox LXC. See details in [Hardware Acceleration](./hardware-acceleration.md) section.

## Which Installation Method to Choose?

### Docker (Recommended)
- **Best for**: Most users, easy setup and updates
- **Pros**: Simple installation, isolated environment, easy updates
- **Cons**: Container overhead, complex GPU passthrough in some environments

### Bare Metal
- **Best for**: Advanced users, GPU acceleration in LXC, performance-critical deployments
- **Pros**: Direct hardware access, better performance, native GPU support
- **Cons**: More complex setup, manual updates, less isolation

### Installation Method Comparison

| Feature | Docker | Bare Metal |
|---------|--------|------------|
| Setup Difficulty | Easy | Moderate |
| Update Process | Simple | Manual |
| Resource Usage | Higher | Lower |
| Hardware Access | Limited | Full |
| GPU in LXC | Complex | Native |
| Isolation | Complete | Process-level |

Each method has its own set of instructions, so choose the one that best fits your setup.

It is recommended to use Docker Compose for most installations, as it simplifies the process of managing containers and configurations. Choose bare metal installation if you need direct hardware access or are running in environments where Docker GPU passthrough is problematic (such as Proxmox LXC containers).

!!! tip
    There are some things you need to know for installing Trailarr, which are explained in [Docker Compose](./docker-compose.md) section. Please read that section before proceeding with the installation.