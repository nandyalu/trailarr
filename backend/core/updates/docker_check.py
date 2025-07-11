import aiohttp
import asyncio

from app_logger import ModuleLogger
from config.settings import app_settings

logger = ModuleLogger("UpdateChecker")


async def get_latest_image_version(image_name: str) -> str | None:
    """Gets the latest release tag from Github API asynchronously.
    Args:
        image_name (str): The name of the Docker image on Docker Hub. \n
            Example: "library/ubuntu" \n
    Returns:
        str|None: The latest release tag of the image.\n
            Example: "v0.2.0"
    """
    url = f"https://api.github.com/repos/{image_name}/releases/latest"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                release_data = await response.json()
                return release_data["tag_name"]
    except Exception as e:
        logger.error(f"Error fetching release info from Github API: {e}")
        return None


def get_current_image_version():
    """Gets the current version of the image running in the container."""
    # Implement logic to get the current image version
    # This could be an environment variable or a file in your container
    return app_settings.version


async def check_for_update():
    image_name = "nandyalu/trailarr"
    current_version = get_current_image_version()
    latest_version = await get_latest_image_version(image_name)

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
    asyncio.run(check_for_update())
