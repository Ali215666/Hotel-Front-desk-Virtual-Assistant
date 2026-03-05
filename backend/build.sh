#!/bin/bash
# Build script for Hotel AI Backend Docker image

set -e

echo "================================"
echo "Building Hotel AI Backend Docker Image"
echo "================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="hotel-ai-backend"
VERSION="1.0.0"

echo -e "${YELLOW}Building image: ${IMAGE_NAME}:${VERSION}${NC}"

# Build from backend directory
cd "$(dirname "$0")"

# Build the image
docker build -t ${IMAGE_NAME}:${VERSION} -t ${IMAGE_NAME}:latest .

echo -e "${GREEN}✓ Build complete!${NC}"
echo ""
echo "Run the container with:"
echo "  docker run -p 8000:8000 ${IMAGE_NAME}:latest"
echo ""
echo "Or use docker-compose:"
echo "  docker-compose up -d"
echo ""
echo "Check health:"
echo "  curl http://localhost:8000/health"
