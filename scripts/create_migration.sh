#!/bin/bash

# This script is intended to be run in a Docker container for Trailarr.
# It creates a new migration using Alembic.

# Move the existing database to a temporary location
echo "Moving existing database to temporary location..."
if [ ! -d /config ]; then
  echo "Configuration directory /config does not exist. Exiting."
  exit 1
fi

# Change to the backend directory where Alembic is configured
echo "Changing to backend directory..."
cd /app/backend

# Check if there is an existing database file and back it up
if [ -f /config/trailarr.db ]; then
  echo "Copying database file '/config/trailarr.db' to '/config/trailarr_old.db'."
  cp /config/trailarr.db /config/trailarr_old.db
  # Run Alembic upgrade to the latest version
  echo "Running Alembic upgrade to the latest version..."
  alembic upgrade head
else
  echo "Database file '/config/trailarr.db' does not exist!"
  echo "You need to revert all model changes before creating a migration, in order to create a new database and apply existing migrations."
  # Wait for user input before continuing
  read -p "Revert changes to models and Press Enter to continue or Ctrl+C to exit..."
  # Run Alembic upgrade to the latest version
  echo "Running Alembic upgrade to create a database and upgrade to the latest version..."
  alembic upgrade head
  echo "Database created and upgraded to the latest version. Make the necessary model changes before running this script again."
  exit 0
fi

# Get migration message from user input
echo "Enter migration message:"
read migration_message
if [ -z "$migration_message" ]; then
  echo "Migration message cannot be empty. Restoring original database and exiting."
  rm /config/trailarr.db
  mv /config/trailarr_old.db /config/trailarr.db
  exit 1
fi
# Create a new migration with the provided message
echo "Creating new migration with message: $migration_message"
alembic revision --autogenerate -m "$migration_message"

# Restore the original database file
rm /config/trailarr.db
mv /config/trailarr_old.db /config/trailarr.db

# Run the Alembic upgrade to apply the new migration
alembic upgrade head

# Notify the user that the migration has been created
echo "Migration '$migration_message' created and applied successfully."