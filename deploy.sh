#!/bin/bash

ROOT_DIR="$HOME/docker"
APP_NAME="elginvault"
API_HOST="elginvault-api"
API_PORT=8000
DB_HOST="elginvault-db"
DB_PORT=5432
DB_DBNAME="postgres"
DB_USER="postgres"


# Help function
function usage() {
  echo "Usage: $0 [options]"
  echo "Options:"
  echo "  -d, --dir <path>      Specify the root directory (default: ~/docker)"
  echo "  -p, --port <port>     Specify the port to expose (default: 8000)"
  echo "  -h, --help            Show this help message"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -d|--dir)
      ROOT_DIR="$2"
      shift
      ;;
    -p|--port)
      API_PORT="$2"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      usage
      exit 1
      ;;
  esac
  shift
done

# Check if the root directory exists
if [ ! -d "$ROOT_DIR" ]; then
  echo "Creating root directory: $ROOT_DIR"
  mkdir -p "$ROOT_DIR"
fi

DEPLOY_DIR="$ROOT_DIR/$APP_NAME"

# Check if the folder already exists
if [ -d "$DEPLOY_DIR" ]; then
  echo "Found existing folder: $DEPLOY_DIR. Please remove it before deploying."
  echo "Aborted."
  exit 1
fi

# Prompt for the database password
read -p "Enter the database password for $DB_USER@$DB_HOST: " DB_PASSWORD
echo ""
if [ -z "$DB_PASSWORD" ]; then
  echo "Error: Database password cannot be empty."
  exit 1
fi

# Create the deployment directory
echo "Creating deployment directory: $DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"

# Copy config.ini and .env.example to the deployment folder
echo "Copying config.ini and .env.example to $DEPLOY_DIR"
cp config.ini "$DEPLOY_DIR/"
cp .env.example "$DEPLOY_DIR/.env"

# Fill in .env with database connection details
echo "Configuring .env file in $DEPLOY_DIR/.env"
sed -i "s/^DB_HOST=.*/DB_HOST=$DB_HOST/" "$DEPLOY_DIR/.env"
sed -i "s/^DB_PORT=.*/DB_PORT=$DB_PORT/" "$DEPLOY_DIR/.env"
sed -i "s/^DB_DBNAME=.*/DB_DBNAME=$DB_DBNAME/" "$DEPLOY_DIR/.env"
sed -i "s/^DB_USER=.*/DB_USER=$DB_USER/" "$DEPLOY_DIR/.env"
sed -i "s/^DB_PASSWORD=.*/DB_PASSWORD=$DB_PASSWORD/" "$DEPLOY_DIR/.env"

# Generate compose.yaml from the template
TEMPLATE_FILE="docker/compose.yaml.template"
COMPOSE_FILE="$DEPLOY_DIR/compose.yaml"
echo "Generating compose.yaml from template: $TEMPLATE_FILE"
#sed "s/{{PORT}}/$API_PORT/g" "$TEMPLATE_FILE" > "$COMPOSE_FILE"
sed -e "s/{{API_HOST}}/$API_HOST/g" \
    -e "s/{{API_PORT}}/$API_PORT/g" \
    -e "s/{{DB_HOST}}/$DB_HOST/g" \
    -e "s/{{DB_PORT}}/$DB_PORT/g" \
    -e "s/{{DB_PASSWORD}}/$DB_PASSWORD/g" \
    "$TEMPLATE_FILE" > "$COMPOSE_FILE"
if [ $? -ne 0 ]; then
  echo "Error: Failed to generate compose.yaml from template."
  exit 1
fi

# Instructions for the user
echo ""
echo "Deployment setup complete."
echo "Configure DB_PASSWORD environment variable in compose.yaml."
echo "Configure .env file in $DEPLOY_DIR/.env with your settings."
echo "Run the following command to start the container:"
echo "  docker compose up -d"
