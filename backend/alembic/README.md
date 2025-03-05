Generic single-database configuration.

For future releases/migrations if any changes were made to database models, run the following in devcontainer:

1. Rename the database file `/config/trailarr.db` to `/config/trailarr_old.db`.
    >>>> mv /config/trailarr.db /config/trailarr_old.db

2. Run alembic upgrade head command to create a new database file `/config/trailarr.db` with all existing migrations.
    >>>> cd backend
    >>>> alembic upgrade head

3. Run alembic create migration command to create a new migration.
    >>>> cd backend
    >>>> alembic revision --autogenerate -m "With an appropriate message"

4. Delte the `/config/trailarr.db` file that was created in step 2.
    >>>> rm /config/trailarr.db

5. Restore the database file `/config/trailarr_old.db` to `/config/trailarr.db`.
    >>>> mv /config/trailarr_old.db /config/trailarr.db

6. Now run `/app/scripts/start.sh` to run migrations on existing database. Ensure that the database migrations are successful. Test the application to ensure that the changes are working as expected.
