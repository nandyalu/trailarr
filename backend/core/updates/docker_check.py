import requests

from app_logger import ModuleLogger
from config.settings import app_settings

logger = ModuleLogger("UpdateChecker")


def get_image_versions(image_name):
    """Gets all available versions of a Docker image from Docker Hub.\n
    Args:
        image_name (str): The name of the Docker image on Docker Hub. \n
            Example: "library/ubuntu" \n
    Returns:
        list: A list of dictionaries containing the
            name, digest, and release date of each version.\n
            Example: \n
                [{"name": "0.1.0", "digest": "sha256:...", "released": "2021-08-01T12:00:00Z"}]
    """
    try:
        # Get all tags for the image from Docker Hub
        url = f"https://registry.hub.docker.com/v2/repositories/{image_name}/tags/"
        response = requests.get(url)
        tags = response.json()["results"]
        all_versions = [
            {
                "name": str(tag["name"]),
                "digest": str(tag["digest"]),
                "released": str(tag["last_updated"]),
            }
            for tag in tags
        ]
    except Exception:
        all_versions = []
    return all_versions


def get_current_image_version():
    """Gets the current version of the image running in the container."""
    # Implement logic to get the current image version
    # This could be an environment variable or a file in your container
    return app_settings.version


def get_latest_version_info(all_versions: list[dict[str, str]]):
    """Gets the latest version info from the list of all versions. \n
    Args:
        all_versions (list): A list of dictionaries containing the \
            name, digest, and release date of each version.\n
            Example: \n
            [ {"name": "1.0.2", "digest": "sha256:...", "released": "2021-08-10T12:00:00Z"}, \n
                {"name": "1.0.1", "digest": "sha256:...", "released": "2021-08-01T12:00:00Z"} ] \n
    Returns:
        tuple: A tuple containing the digest and name of the latest version.\n
            Example: ("sha256:...", "0.2.0")
    """
    latest_digest = ""
    latest_version = ""
    for version in all_versions:
        if version["name"] == "latest":
            latest_digest = version["digest"]
            latest_version = version["name"]
        if latest_digest:
            if version["name"] == "latest":
                continue
            if version["digest"] == latest_digest:
                latest_version = version["name"]
                break
    return latest_digest, latest_version


def get_current_version_digest(
    all_versions: list[dict[str, str]], current_version: str
):
    """Gets the digest for the current version."""
    for version in all_versions:
        if version["name"] == current_version:
            return version["digest"]
    return ""


def check_for_update():
    image_name = "nandyalu/trailarr"
    current_version = get_current_image_version()
    all_versions = get_image_versions(image_name)

    latest_digest, latest_version = get_latest_version_info(all_versions)
    current_digest = get_current_version_digest(all_versions, current_version)

    if not latest_digest or not current_digest:
        logger.error("Error: Could not update details from Docker Hub.")
        return

    if latest_digest != current_digest:
        logger.info(
            f"A newer version ({latest_version}) of the image is available. Please update!"
        )
        app_settings.update_available = True
    else:
        logger.info(
            f"You are using the latest version ({current_version}) of the image."
        )


if __name__ == "__main__":
    check_for_update()
