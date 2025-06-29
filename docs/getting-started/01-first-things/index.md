# First Things
First things first! Before you can start using Trailarr, ensure you have installed the pre-requisites and configured your environment correctly. 

## Prerequisites
To run and make use of Trailarr, you need the following installed on your system:

- Docker: [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/){:target="_blank"}
- Docker Compose (optional, but recommended): [https://docs.docker.com/compose/install/](https://docs.docker.com/compose/install/){:target="_blank"}
- Radarr: [https://radarr.video/](https://radarr.video/){:target="_blank"}
- Sonarr: [https://sonarr.tv/](https://sonarr.tv/){:target="_blank"}

!!! tip ""
    *Rest of the Tutorial assumes you have these installed and running on your system. If you haven't set up Radarr and Sonarr yet, please refer to their respective documentation for installation instructions.

We recommend you to glance through these once, even if you are familiar with Docker containers, so that you get an understanding of what these do and how Trailarr uses them, especially the [Radarr/Sonarr Volumes](./radarr-sonarr-volumes.md) section! 

## Getting Started
A Docker container is like an app on your phone. It comes with everything it needs to run.

Just like an app on your phone, Docker containers are isolated and does not have access to your computer settings and files, so we need to explicitly provide them. We can do that using `Environment Variables` and `Volume Mappings`.

### Environment Variables

- Environment variables are like settings for your app. Most of the Trailarr settings can be configured after you install it, but some need to be set before you start the container. 

- For example, Docker containers does not have access to your computer's timezone. So, you can use environment variables to set the timezone and other settings for Trailarr.

You can find the available options and what they do in [Environment Variables](./environment-variables.md) page.

### Volume Mappings

- Just like you need to provide permissions for an app to access your photos or other files, you need to give Trailarr access to your media files.

- Docker uses **volume mappings** to link folders on your computer to folders inside the Trailarr container. This way, Trailarr can see your media files and save trailers alongside them.

- Unlike providing access to your photos or media files to an app, you also need to tell Docker where to put that folder inside container.

In simple words, Volume mapping links a folder on your host machine to a folder inside the Docker container. This allows data to persist even if the container is stopped or removed.

For Trailarr to access your media files (to find existing trailers) and to save trailer files alongside your media (depending on your setup), it needs to know where your Radarr and Sonarr media folders are located *from Trailarr's perspective*.

Let's find them before proceeding further! See [Radarr-Sonarr-Volumes](./radarr-sonarr-volumes.md).

