#!/bin/bash
set -e

DOCKERHUB_USER="ryany1819"
IMAGE_NAME="${DOCKERHUB_USER}/elginvault-api"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)

# Help function
function usage() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -t, --tag <tag>   Specify the Docker image tag (default: latest)"
    echo "  -h, --help        Show this help message"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--tag)
            IMAGE_TAG="$2"
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
if [ ! -n "$IMAGE_TAG" ]; then
    IMAGE_TAG=$(date +'%y.%m.%d')
    echo "No tag specified. Using auto-generated tag: $TAG"
fi

# Check if the image already exists
EXISTING_IMAGE=$(docker images -q ${IMAGE_NAME})
if [ -n "$EXISTING_IMAGE" ]; then
    echo "Image ${IMAGE_NAME} already exists. Removing it..."

    # Remove any containers using the image (active or inactive)
    CONTAINERS=$(docker ps -a -q --filter ancestor=${IMAGE_NAME})
    if [ -n "$CONTAINERS" ]; then
        echo "Stopping and remvoving containers using the image..."
        docker rm -f $CONTAINERS
    fi

    # Remove the existing image
    docker rmi -f $EXISTING_IMAGE
    if [ $? -ne 0 ]; then
        echo "Failed to remove existing image: ${IMAGE_NAME}"
        exit 1
    fi
fi

# Copy pyproject.toml and pyproject.lock to the current directory
TMP_CTX=$(mktemp -d)
mkdir -p "$TMP_CTX"
cp "$PROJECT_ROOT/pyproject.toml" \
    "$PROJECT_ROOT/poetry.lock" \
    "$PROJECT_ROOT/app" -r \
    "$PROJECT_ROOT/db" -r \
    "$TMP_CTX"
if [ $? -ne 0 ]; then
    echo "Failed to copy files to temporary context."
    exit 1
fi

# Build the Docker image
echo "Building Docker image: $IMAGE_NAME:$IMAGE_TAG..."
docker build \
    -t $IMAGE_NAME:$IMAGE_TAG \
    -f "$SCRIPT_DIR/Dockerfile" \
    "$TMP_CTX"

# Remove the temporary build context
rm -rf "$TMP_CTX"

if [ $? -eq 0 ]; then
    echo "Docker image built successfully: $IMAGE_NAME:$IMAGE_TAG"
else
    echo "Failed to build Docker image: $IMAGE_NAME:$IMAGE_TAG"
    exit 1
fi

# Remove the copied files
# rm "$SCRIPT_DIR/pyproject.toml" "$SCRIPT_DIR/poetry.lock"
# if [ $? -ne 0 ]; then
#   echo "Failed to remove copied files."
#   exit 1
# fi

# Tag the image as "latest"
echo "Tagging image $IMAGE_NAME:$IMAGE_TAG as $IMAGE_NAME:latest..."
docker tag $IMAGE_NAME:$IMAGE_TAG $IMAGE_NAME:latest
if [ $? -ne 0 ]; then
  echo "Failed to tag image as latest."
  exit 1
fi

# Push both tags to Docker Hub
echo "Pushing image $IMAGE_NAME:$IMAGE_TAG to Docker Hub..."
docker push $IMAGE_NAME:$IMAGE_TAG
if [ $? -ne 0 ]; then
  echo "Failed to push image with tag $IMAGE_TAG."
  exit 1
fi

echo "Pushing image $IMAGE_NAME:latest to Docker Hub..."
docker push $IMAGE_NAME:latest
if [ $? -ne 0 ]; then
  echo "Failed to push image with tag latest."
  exit 1
fi

echo "Image $IMAGE_NAME:$IMAGE_TAG successfully built and pushed."