#!/bin/bash

# Check POSTGRES_PASSWORD environment variable (required by TimescaleDB Docker image)
if [ -z "$POSTGRES_PASSWORD" ]; then
  echo "Error: POSTGRES_PASSWORD environment variable is not set."
  exit 1
fi

# Start PostgreSQL/TimescaleDB in the foreground
docker-entrypoint.sh postgres &

# Wait for the database to be ready
echo "Waiting for TimescaleDB to be ready..."
until pg_isready -U postgres -d postgres; do
  sleep 5
done

FLAG_FILE="/var/lib/postgresql/data/.initialized"
if [ ! -f "$FLAG_FILE" ]; then
  echo "Initializing database tables..."
  # Execute SQL script using psql (PGPASSWORD is required by psql)
  PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "$HOSTNAME" -p 5432 -U postgres -d postgres -f /create_tables.sql

  if [ $? -eq 0 ]; then
    echo "Database tables initialized successfully."
    # Create the flag file to indicate initialization is complete
    touch "$FLAG_FILE"
  else
    echo "Error initializing database tables."
    exit 1
  fi
else
  echo "Database tables already initialized. Skipping initialization."
fi

# Bring PostgreSQL to the foreground
wait
