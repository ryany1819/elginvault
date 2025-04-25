#!/bin/bash

check_env_file() {
    if [[ ! -f ".env" ]]; then
        echo "Error: .env file not found. Please create it before running this script."
        exit 1
    fi
}

test_db_connectivity() {
    echo "Testing database connectivity..."
    source .env

    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_DBNAME -c '\q' > /dev/null 2>&1
    if [[ $? -ne 0 ]]; then
        echo "Error: Failed to connect to the database using the parameters in .env."
        exit 1
    fi

    echo "Database connectivity test successful."
}

check_env_file
test_db_connectivity

echo "Launching FastAPI application..."
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload