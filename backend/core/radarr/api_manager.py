from typing import Any
from backend.exceptions import InvalidResponseError
from backend.core.base.arr_manager.base import AsyncBaseArrManager


class RadarrManager(AsyncBaseArrManager):
    APPNAME = "Radarr"

    def __init__(self, url: str, api_key: str):
        """
        Constructor for connection to Radarr API

        Args:
            url (str): Host URL to Radarr API
            api_key (str): API Key for Radarr API

        Returns:
            None
        """
        self.version = "v3"
        super().__init__(url, api_key, self.version)

    async def get_system_status(self) -> str:
        """Get the system status of the Radarr API

        Args:
            None

        Returns:
            str: The status of the Radarr API with version if successful.

        Raises:
            ConnectionError: If the connection is refused / response is not 200
            ConnectionTimeoutError: If the connection times out
            InvalidResponseError: If API response is invalid
        """
        return await self._get_system_status(self.APPNAME)

    # Define Radarr specific API methods here
    async def get_all_movies(self) -> list[dict[str, Any]]:
        """Get a movie from the Arr API

        Args:
            movie_id (int): The ID of the movie to get

        Returns:
            list[dict[str, Any]: List of movies from the Radarr API

        Raises:
            ConnectionError: If the connection is refused / response is not 200
            ConnectionTimeoutError: If the connection times out
            InvalidResponseError: If the API response is invalid
        """
        movies = await self._request("GET", f"/api/{self.version}/movie")
        if isinstance(movies, list):
            return movies
        raise InvalidResponseError("Invalid response from Radarr API")

    async def get_movie(self, radarr_id: int) -> dict[str, Any]:
        """Get a movie from the Arr API

        Args:
            radarr_id (int): The ID of the movie to get

        Returns:
            dict[str, Any]: Movie from the Radarr API

        Raises:
            ConnectionError: If the connection is refused / response is not 200
            ConnectionTimeoutError: If the connection times out
            InvalidResponseError: If the API response is invalid
        """
        movie = await self._request("GET", f"/api/{self.version}/movie/{radarr_id}")
        if isinstance(movie, dict):
            return movie
        raise InvalidResponseError("Invalid response from Radarr API")

    # Define Alias methods here!
    get_all_media = get_all_movies
    get_media = get_movie
