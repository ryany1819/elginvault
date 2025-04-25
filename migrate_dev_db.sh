#!/bin/bash
set -e

# Function to print usage instructions
print_usage() {
    echo "Usage: $0 <init|upgrade> [args...]"
    echo ""
    echo "Modes:"
    echo "  init    Initialize a new development database."
    echo "          Requires the following arguments:"
    echo "            [host] [port] <user> <password>"
    echo "          Defaults:"
    echo "            host: localhost"
    echo "            port: 8001"
    echo ""
    echo "  upgrade Upgrade the existing development database."
    echo "          Reuses existing .env configuration except for DB_DBNAME."
    echo "          Requires no additional arguments."
    echo ""
    echo "Examples:"
    echo "  $0 init postgres mypassword"
    echo "  $0 init 127.0.0.1 8001 postgres mypassword"
    echo "  $0 upgrade"
}

# Function to generate a unique database name
generate_db_name() {
    echo "db_$(uuidgen | cut -d'-' -f1)"
}

# Function to create or update the .env file
create_env_file() {
    local host=$1
    local port=$2
    local user=$3
    local password=$4
    local db_name=$5

    # Load the .env.example template
    if [[ ! -f .env.example ]]; then
        echo "Error: .env.example file not found."
        exit 1
    fi

    # Replace placeholders in the .env.example template and save as .env
    sed -e "s/^DB_HOST=.*/DB_HOST=$host/" \
        -e "s/^DB_PORT=.*/DB_PORT=$port/" \
        -e "s/^DB_USER=.*/DB_USER=$user/" \
        -e "s/^DB_PASSWORD=.*/DB_PASSWORD=$password/" \
        .env.example > .env
}

# Function to update the DB_DBNAME in the existing .env file
update_env_dbname() {
    local dbname=$1
    if [[ ! -f .env ]]; then
        echo "Error: .env file not found. Please run 'init' mode first."
        exit 1
    fi
    sed -i "s/^DB_DBNAME=.*/DB_DBNAME=$dbname/" .env
}

# Function to run create_tables.sql using psql
run_create_tables() {
    local dbname=$1

    # Source the .env file to load environment variables
    source .env

    # Connect to the database server to create/recreate the database
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "DROP DATABASE IF EXISTS $dbname;"
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "CREATE DATABASE $dbname;"

    # Apply the create_tables.sql file to the new database
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $dbname -f db/migrations/create_tables.sql
    if [[ $? -ne 0 ]]; then
        echo "Error: Failed to apply create_tables.sql."
        exit 1
    fi
    echo "Database $dbname created and tables initialized successfully."
}

# Main script logic
if [[ $# -lt 1 ]]; then
    print_usage
    exit 1
fi

MODE=$1

if [[ $MODE == "init" ]]; then
    # Ensure at least user and password are provided
    if [[ $# -lt 3 ]]; then
        print_usage
        exit 1
    fi

    # Set defaults for host and port
    HOST=${2:-localhost}
    PORT=${3:-8001}
    USER=$4
    PASSWORD=$5

    # Validate user and password
    if [[ -z $USER || -z $PASSWORD ]]; then
        echo "Error: Both user and password must be provided for 'init' mode."
        exit 1
    fi

    # Generate a unique database name
    DB_NAME=$(generate_db_name)
    echo "Generated database name: $DB_NAME"

    # Create the .env file
    create_env_file $HOST $PORT $USER $PASSWORD $DBNAME

    # Run create_tables.sql
    run_create_tables $DB_NAME

    echo "Database initialized successfully with name: $DB_NAME"
elif [[ $MODE == "upgrade" ]]; then
    # Ensure the .env file exists
    if [[ ! -f .env ]]; then
        echo "Error: .env file not found. Please run 'init' mode first."
        exit 1
    fi

    # Source the .env file to load environment variables
    source .env

    # Generate a unique database name
    DB_NAME=$(generate_db_name)
    echo "Generated database name: $DB_NAME"

    # Update the .env file with the new database name
    update_env_dbname $DB_NAME

    # Run create_tables.sql
    run_create_tables $DB_NAME

    echo "Database upgraded successfully with name: $DB_NAME"
else
    echo "Error: Invalid mode '$MODE'."
    print_usage
    exit 1
fi