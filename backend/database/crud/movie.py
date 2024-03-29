from datetime import datetime
import logging
import re
from typing import Optional
from typing import Sequence
from sqlmodel import Session, col, desc, select, or_
from backend.database.crud.connection import ConnectionDatabaseHandler
from backend.database.models.movie import Movie, MovieCreate, MovieRead, MovieUpdate
from backend.database.utils.engine import manage_session
from backend.exceptions import ItemNotFoundError


class MovieDatabaseHandler:
    """CRUD operations for movie database table."""

    NO_MOVIE_MESSAGE = "Movie not found. Movie id: {} does not exist!"
    NO_CONN_MESSAGE = "Connection not found. Connection id: {} does not exist!"

    def _create_or_update(
        self, movie: MovieCreate, _session: Session
    ) -> tuple[Movie, bool, bool]:
        """-->>This is a private method<<-- \n
        Create or update a movie in the database. \n
        If a movie already exists, it will be updated, otherwise it will be created.\n
        Args:
            movie (MovieCreate): The movie to create or update.
            _session (Session): A session to use for the database connection.\n
        Returns:
            tuple[Movie, bool, bool]: Movie object and flags indicating created and updated.\n
            Example::\n
                (<Movie obj>, True)
        """
        # Radarr id will be unique for every movie in the same connection
        # So, we can use it to check if the movie already exists in the database
        # If it does, we will update it, otherwise we will create it
        db_movie = self._read_if_exists(
            movie.connection_id, movie.radarr_id, _session=_session
        )
        if db_movie:
            # Exists, update it
            movie_update_data = movie.model_dump(exclude_unset=True)
            db_movie.sqlmodel_update(movie_update_data)
            if _session.is_modified(db_movie):
                db_movie.updated_at = datetime.now()
                return db_movie, False, True
            # Already in session, no need to add it again
            return db_movie, False, False
        else:
            # Doesn't exist, create it
            db_movie = Movie.model_validate(movie)
            _session.add(db_movie)
            return db_movie, True, False

    @manage_session
    def create_or_update_bulk(
        self,
        movies: list[MovieCreate],
        *,
        _session: Session = None,  # type: ignore
    ) -> list[tuple[MovieRead, bool]]:
        """Create or update multiple movies in the database at once. \n
        If a movie already exists, it will be updated, otherwise it will be created.\n
        Args:
            movies (list[MovieCreate]): The list of movies to create or update.
            _session (optional): A session to use for the database connection. \
                Defaults to None, in which case a new session is created. \n
        Returns:
            list[tuple[MovieRead, bool]]: List of tuples with MovieRead object and created flag \n
            Example:: \n
                [(<MovieRead obj 1>, True), (<MovieRead obj 2>, False), ...] \n
        Raises:
            ItemNotFoundError: If any of the connections with provided connection_id's are invalid.
            ValidationError: If any of the movies are invalid.
        """
        self._check_connection_exists_bulk(movies, _session=_session)
        db_movies: list[tuple[Movie, bool]] = []
        new_count: int = 0
        updated_count: int = 0
        for movie in movies:
            db_movie, _created, _updated = self._create_or_update(
                movie, _session=_session
            )
            if _created:
                new_count += 1
            if _updated:
                updated_count += 1
            db_movies.append((db_movie, _created))
        _session.commit()
        logging.info(f"Movies created: {new_count}, Movies updated: {updated_count}")
        return [
            (MovieRead.model_validate(db_movie), _created)
            for db_movie, _created in db_movies
        ]

    @manage_session
    def _read_if_exists(
        self,
        connection_id: int,
        radarr_id: int,
        *,
        _session: Session = None,  # type: ignore
    ) -> Optional[Movie]:
        """-->>This is a private method<<-- \n
        Check if a movie exists in the database for any given connection and radarr ids.\n
        Args:
            connection_id (int): The id of the connection to check.
            radarr_id (int): The radarr id of the movie to check.
            _session (optional): A session to use for the database connection. \
                Defaults to None, in which case a new session is created.\n
        Returns:
            Optional[Movie]: The movie object if it exists, None otherwise.
        """
        statement = (
            select(Movie)
            .where(Movie.connection_id == connection_id)
            .where(Movie.radarr_id == radarr_id)
        )
        db_movie = _session.exec(statement).one_or_none()
        return db_movie

    @manage_session
    def _get_db_item(
        self,
        movie_id: int,
        *,
        _session: Session = None,  # type: ignore
    ) -> Movie:
        """-->>This is a private method<<-- \n
        Get a movie from the database.

        Args:
            movie_id (int): The id of the movie to read.
            _session (optional): A session to use for the database connection. \
                Defaults to None, in which case a new session is created.

        Returns:
            Movie: The movie object.

        Raises:
            ItemNotFoundError: If a movie with provided id does not exist.
        """
        db_movie = _session.get(Movie, movie_id)
        if not db_movie:
            raise ItemNotFoundError("Movie", movie_id)
        return db_movie

    @manage_session
    def read(
        self,
        movie_id: int,
        *,
        _session: Session = None,  # type: ignore
    ) -> MovieRead:
        """Read a movie from the database.

        Args:
            movie_id (int): The id of the movie to read.
            _session (optional): A session to use for the database connection. \
                Defaults to None, in which case a new session is created.

        Returns:
            MovieRead: The read-only movie object.

        Raises:
            ItemNotFoundError: If a movie with provided id does not exist.
        """
        db_movie = self._get_db_item(movie_id, _session=_session)
        # Convert the database model (Movie) to read-only model (MovieRead) to return
        movie = MovieRead.model_validate(db_movie)
        return movie

    @manage_session
    def read_all(
        self,
        *,
        _session: Session = None,  # type: ignore
    ) -> list[MovieRead]:
        """Read all movies from the database.

        Args:
            _session (optional): A session to use for the database connection. \
                Defaults to None, in which case a new session is created.

        Returns:
            list[MovieRead]: The list of movie[read] objects.
        """
        results = _session.exec(select(Movie))
        movies_results = results.all()
        return self._convert_to_read_list(movies_results)

    @manage_session
    def read_all_by_connection(
        self,
        connection_id: int,
        *,
        _session: Session = None,  # type: ignore
    ) -> list[MovieRead]:
        """Read all movies from the database by connection id.

        Args:
            connection_id (int): The id of the connection to filter movies.
            _session (optional): A session to use for the database connection. \
                Defaults to None, in which case a new session is created.

        Returns:
            list[MovieRead]: The list of movie[read] objects.
        """
        statement = select(Movie).where(Movie.connection_id == connection_id)
        results = _session.exec(statement)
        movies_results = results.all()
        return self._convert_to_read_list(movies_results)

    @manage_session
    def read_recent(
        self,
        offset: int = 0,
        limit: int = 100,
        *,
        _session: Session = None,  # type: ignore
    ) -> list[MovieRead]:
        """Read movies from the database with offset and limit (recently added first).

        Args:
            offset (int): The number of records to skip.
            limit (int): The number of records to return. Max 100.
            _session (optional): A session to use for the database connection. \
                Defaults to None, in which case a new session is created.

        Returns:
            list[MovieRead]: The list of movie[read] objects.
        """
        offset = max(offset, 0)
        limit = max(1, min(limit, 100))

        statement = (
            select(Movie).offset(offset).limit(limit).order_by(desc(Movie.added_at))
        )
        results = _session.exec(statement)
        movies_results = results.all()
        return self._convert_to_read_list(movies_results)

    @manage_session
    def search(
        self,
        query: str,
        *,
        _session: Session = None,  # type: ignore
    ) -> list[MovieRead]:
        """Search movies from the database by title, overview, imdb id, or tmdb id.
        If an exact match is found for imdb id or tmdb id, it will return only that movie.
        If a 4 digit number is found in the query, it will return movies from that year only.
        Otherwise, it will return a list of movies matching the query. Recently added first, 50 max.

        Args:
            query (str): The search query.
            _session (optional): A session to use for the database connection. \
                Defaults to None, in which case a new session is created.

        Returns:
            list[MovieRead]: The list of movie[read] objects.
        """
        if not query:
            return []
        # check if imdb id, tmdb id or year is present in the query
        imdb_id = self._extract_imdb_id(query)
        tmdb_id = self._extract_tmdb_id(query) if not imdb_id else None
        year = (
            self._extract_four_digit_number(query)
            if not imdb_id and not tmdb_id
            else None
        )

        statement = select(Movie)
        if imdb_id:
            statement = statement.where(Movie.imdb_id == imdb_id)
        elif tmdb_id:
            statement = statement.where(Movie.tmdb_id == tmdb_id)
        else:
            if year:
                query = query.replace(year, "").strip().replace("  ", " ")
                statement = statement.where(Movie.year == year)
            statement = (
                statement.where(
                    or_(
                        col(Movie.title).ilike(query),
                        col(Movie.overview).ilike(query),
                    )
                )
                .limit(50)
                .order_by(desc(Movie.added_at))
            )
        results = _session.exec(statement)
        movies_results = results.all()
        return self._convert_to_read_list(movies_results)

    @manage_session
    def update(
        self,
        movie_id: int,
        movie: MovieUpdate,
        *,
        _session: Session = None,  # type: ignore
    ) -> bool:
        """Update an existing movie in the database.

        Args:
            movie_id (int): The id of the movie to update.
            movie (MovieUpdate): The movie data to update.
            _session (optional): A session to use for the database connection. \
                Defaults to None, in which case a new session is created.

        Returns:
            bool: True if movie update is successful.

        Raises:
            ItemNotFoundError: If a movie with provided id does not exist.
        """
        # Get the movie from the database
        db_movie = self._get_db_item(movie_id, _session=_session)
        # Update the movie details from input
        movie_update_data = movie.model_dump(exclude_unset=True)
        db_movie.sqlmodel_update(movie_update_data)

        # Check if the connection exists
        self._check_connection_exists(db_movie.connection_id, _session=_session)

        # Commit the changes to the database
        _session.add(db_movie)
        _session.commit()
        return True

    @manage_session
    def delete(
        self,
        movie_id: int,
        *,
        _session: Session = None,  # type: ignore
    ) -> bool:
        """Delete an existing movie from the database.

        Args:
            movie_id (int): The id of the movie to delete.
            _session (optional): A session to use for the database connection. \
                Defaults to None, in which case a new session is created.

        Returns:
            bool: True if movie deletion is successful.

        Raises:
            ItemNotFoundError: If a movie with provided id does not exist.
        """
        movie_db = self._get_db_item(movie_id, _session=_session)
        _session.delete(movie_db)
        _session.commit()
        return True

    @manage_session
    def delete_bulk(
        self,
        movie_ids: set[int],
        *,
        _session: Session = None,  # type: ignore
    ) -> bool:
        """Delete multiple existing movies from the database at once. \n
        If a movie with provided id does not exist, it will be skipped.

        Args:
            movie_ids (list[int]): The list of movie id's to delete.
            _session (optional): A session to use for the database connection. \
                Defaults to None, in which case a new session is created.

        Returns:
            bool: True if all movie deletions are successful.

        Raises:
            None
        """
        for movie_id in movie_ids:
            try:
                movie_db = self._get_db_item(movie_id, _session=_session)
                _session.delete(movie_db)
            except ItemNotFoundError:
                continue
        _session.commit()
        return True

    @manage_session
    def _check_connection_exists(
        self,
        connection_id: int,
        *,
        _session: Session = None,  # type: ignore
    ) -> None:
        """Check if the connection exists in the database.

        Args:
            connection_id (int): The id of the connection to check.
            _session (optional): A session to use for the database connection. \
                Defaults to None, in which case a new session is created.

        Returns:
            None

        Raises:
            ItemNotFoundError: If a connection with provided id does not exist.
        """
        if not ConnectionDatabaseHandler().check_if_exists(
            connection_id, _session=_session
        ):
            raise ItemNotFoundError("Connection", connection_id)

    @manage_session
    def _check_connection_exists_bulk(
        self,
        movies: list[MovieCreate],
        *,
        _session: Session = None,  # type: ignore
    ) -> None:
        """Check if the connections exist in the database.

        Args:
            movies (list[MovieCreate]): The list of movies to check.
            _session (optional): A session to use for the database connection. \
                Defaults to None, in which case a new session is created.

        Returns:
            None

        Raises:
            ItemNotFoundError: If any of the connections with provided id's do not exist.
        """
        connection_ids = {movie.connection_id for movie in movies}
        for connection_id in connection_ids:
            if not ConnectionDatabaseHandler().check_if_exists(
                connection_id, _session=_session
            ):
                raise ItemNotFoundError("Connection", connection_id)

    def _convert_to_read_list(self, movies: Sequence[Movie]) -> list[MovieRead]:
        """Convert a list of Movie to a list of MovieRead."""
        if not movies or len(movies) == 0:
            return []
        movies_read: list[MovieRead] = []
        for movie in movies:
            movies_read.append(MovieRead.model_validate(movie))
        return movies_read

    def _extract_four_digit_number(self, query: str) -> Optional[str]:
        """Extract a 4 digit number from a string."""
        matches = re.findall(r"\b\d{4}\b", query)
        last_match = matches[-1] if matches else None
        return last_match

    def _extract_imdb_id(self, query: str) -> Optional[str]:
        """Extract an imdb id from a string."""
        matches = re.findall(r"tt\d{7,}", query)
        last_match = matches[-1] if matches else None
        return last_match

    def _extract_tmdb_id(self, query: str) -> Optional[str]:
        """Extract a tmdb id from a string."""
        matches = re.findall(r"\b\d{6}\b", query)
        last_match = matches[-1] if matches else None
        return last_match
