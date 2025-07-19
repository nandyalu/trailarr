# Installation

Trailarr can only be installed as a Docker container. We might provide a native installer later, but Docker is the recommended way to run Trailarr, as it allows for easy updates and management.

We have guides for installing Trailarr using these methods:

- [Docker Compose](./docker-compose.md)
- [Docker Run](./docker-run.md)
- [Unraid](./unraid.md)

!!! tip "Hardware Acceleration"
    Trailarr also supports Hardware Acceleration using Intel, AMD, and NVIDIA GPUs for converting downloaded trailers. See details in [Hardware Acceleration](./hardware-acceleration.md) section.

Each method has its own set of instructions, so choose the one that best fits your setup.

It is recommended to use Docker Compose for installation, as it simplifies the process of managing multiple containers and their configurations and/or updating to newer versions later.

!!! tip
    There are some things you need to know for installing Trailarr, which are explained in [Docker Compose](./docker-compose.md) section. Please read that section before proceeding with the installation.