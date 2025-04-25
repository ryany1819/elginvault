#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

API_BUILD_SCRIPT="$SCRIPT_DIR/docker/elginvault-api/build.sh"
DB_BUILD_SCRIPT="$SCRIPT_DIR/docker/elginvault-db/build.sh"

# Usage function
usage() {
    echo "Usage $0 [<tag>]"
    echo "  <tag>: Optional. Specify the version tag for both images (default: auto-generated using YY.MM.DD format)."
    exit 1
}

# Get tag argument or generate auto-tag
if [ $# -eq 1 ]; then
    TAG="$1"
else
    TAG="$(date +'%y.%m.%d')"
    echo "No tag specified. Using auto-generated tag: $TAG"
fi

# Build elginvault-api
echo "Building elginvault-api image with tag $TAG..."
"$API_BUILD_SCRIPT" -t $TAG
if [ $? -ne 0 ]; then
    echo "Failed to build elginvault-api."
    exit 1
fi

# Build elginvault-db
echo "Building elginvault-db image with tag $TAG..."
"$DB_BUILD_SCRIPT" -t $TAG
if [ $? -ne 0 ]; then
    echo "Failed to build elginvault-db."
    exit 1
fi

echo "Both elginvault-api and elginvault-db successfully built with tag $TAG."


