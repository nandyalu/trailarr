import requests

from app_logger import ModuleLogger
from config.settings import app_settings

logger = ModuleLogger("UpdateChecker")


def get_latest_image_version(image_name) -> str | None:
    """Gets the latest release tag from Github API.
    Args:
        image_name (str): The name of the Docker image on Docker Hub. \n
            Example: "library/ubuntu" \n
    Returns:
        str|None: The latest release tag of the image.\n
            Example: "v0.2.0"
    """
    try:
        url = f"https://api.github.com/repos/{image_name}/releases/latest"
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        release_data = response.json()
        return release_data["tag_name"]
    except Exception as e:
        logger.exception(f"Error fetching release info from Github API: {e}")
        return None


def get_current_image_version():
    """Gets the current version of the image running in the container."""
    # Implement logic to get the current image version
    # This could be an environment variable or a file in your container
    return app_settings.version


def check_for_update():
    image_name = "nandyalu/trailarr"
    current_version = get_current_image_version()
    latest_version = get_latest_image_version(image_name)

    if not latest_version:
        return

    if current_version != latest_version:
        logger.info(
            f"A newer version ({latest_version}) of the image is available."
            " Please update!"
        )
        app_settings.update_available = True
    else:
        logger.info(
            f"You are using the latest version ({latest_version}) of the"
            " image."
        )


if __name__ == "__main__":
    check_for_update()
