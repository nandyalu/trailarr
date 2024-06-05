Generic single-database configuration.

For Initial Release, do the following:

1. Delete `versions` folder from `alembic` to remove all existing migrations.

2. Delete the `trailarr.db` file that exists in `backend` folder.

3. Run below command to create first migration:
    >>>> cd backend
    >>>> mkdir alembic/versions
    >>>> alembic revision --autogenerate -m "Initial Release"

    Note: This will create a trailarr.db file in backend folder, no need to copy this to docker image!

4. Build the project. There is a command in `start.sh` that creates necessary folders, runs migrations and creates the database.

For future releases/migrations if any changes were made to database models, run the following:

1. Open `.env` file and comment the line for DATABASE_URL and uncomment the next line to modify `DATABASE_URL`

    from:
        DATABASE_URL='sqlite:////data/trailarr.db'
    to:
        DATABASE_URL='sqlite:///trailarr.db'

2. Run alembic create migration command
    >>>> cd backend
    >>>> alembic revision --autogenerate -m "Release vx.x.x"

    Replace vx.x.x with actual release version.

3. Build the project, `start.sh` in docker image will run migrations on user database.
