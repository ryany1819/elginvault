#!/bin/bash
set -e

# Constants
DOCKERHUB_USER="ryany1819"
IMAGE_NAME="${DOCKERHUB_USER}/elginvault-db"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Usage function
usage() {
  echo "Usage: $0 [options]"
  echo "  -t, --tag <tag>:  Specify the Docker Image tag (default: $(date +'%y.%m.%d'))"
  echo "  -h, --help        Show this help message"
  exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -t|--tag)
      TAG="$2"
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

# Get tag argument or generate auto-tag
if [ -z "$TAG" ]; then
  TAG=$(date +'%y.%m.%d')
  echo "No tag specified. Using auto-generated tag: $TAG"
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
  echo "Docker is not installed or not in PATH. Please install Docker and try again."
  exit 1
fi

# Check if the image already exists
EXISTING_IMAGE=$(docker images -q ${IMAGE_NAME})
if [ -n "$EXISTING_IMAGE" ]; then
  echo "Image ${IMAGE_NAME} already exists. Removing it..."

  # Remove any containers using the image (active or inactive)
  CONTAINERS=$(docker ps -a -q --filter ancestor=${IMAGE_NAME})
  if [ -n "$CONTAINERS" ]; then
    echo "Stopping and removing containers using the image..."
    docker rm -f $CONTAINERS
  fi

  # Remove the existing image
  docker rmi -f $EXISTING_IMAGE
  if [ $? -ne 0 ]; then
    echo "Failed to remove existing image: ${IMAGE_NAME}"
    exit 1
  fi
fi

# Check if create_tables.sql exists
# if [ ! -f "$SCRIPT_DIR/../../db/migrations/create_tables.sql" ]; then
#   echo "Error: create_tables.sql not found in $SCRIPT_DIR/../../db/migrations."
#   exit 1
# fi

# Copy create_tables.sql to the current directory
# echo "Copying create_tables.sql to the current directory..."
# cp "$SCRIPT_DIR/../../db/migrations/create_tables.sql" "$SCRIPT_DIR/create_tables.sql"
# if [ $? -ne 0 ]; then
#   echo "Failed to copy create_tables.sql."
#   exit 1
# fi

# Create a temporary build context
TMP_CTX=$(mktemp -d)
mkdir -p "$TMP_CTX"
cp "$PROJECT_ROOT/db/migrations/create_tables.sql" "$TMP_CTX/create_tables.sql"
cp "$SCRIPT_DIR/entrypoint.sh" "$TMP_CTX/entrypoint.sh"

# Build image
echo "Building image $IMAGE_NAME:$TAG..."
docker build \
  -t $IMAGE_NAME:$TAG \
  -f "$SCRIPT_DIR/Dockerfile" \
  "$TMP_CTX"

# Remove the copied files
rm -rf "$TMP_CTX"

if [ $? -eq 0 ]; then
    echo "Docker image built successfully: $IMAGE_NAME:$IMAGE_TAG"
else
    echo "Failed to build Docker image: $IMAGE_NAME:$IMAGE_TAG"
    exit 1
fi

# Remove create_tables.sql
# rm "$SCRIPT_DIR/create_tables.sql"
# if [ $? -ne 0 ]; then
#   echo "Failed to remove create_tables.sql."
#   exit 1
# fi

# Tag the image as "latest"
echo "Tagging image $IMAGE_NAME:$TAG as $IMAGE_NAME:latest..."
docker tag $IMAGE_NAME:$TAG $IMAGE_NAME:latest
if [ $? -ne 0 ]; then
  echo "Failed to tag image as latest."
  exit 1
fi

# Push both tags to Docker Hub
echo "Pushing image $IMAGE_NAME:$TAG to Docker Hub..."
docker push $IMAGE_NAME:$TAG
if [ $? -ne 0 ]; then
  echo "Failed to push image with tag $TAG."
  exit 1
fi

echo "Pushing image $IMAGE_NAME:latest to Docker Hub..."
docker push $IMAGE_NAME:latest
if [ $? -ne 0 ]; then
  echo "Failed to push image with tag latest."
  exit 1
fi

echo "Image $IMAGE_NAME:$TAG successfully built and pushed."