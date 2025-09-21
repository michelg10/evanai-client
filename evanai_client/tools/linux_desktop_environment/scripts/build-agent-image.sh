#!/bin/bash

# Build script for claude-agent Docker image
# This script:
# 1. Copies the skills directory from reference to build context
# 2. Builds the Docker image with all required tools and packages
# 3. Cleans up temporary files

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${GREEN}=== Building Claude Agent Docker Image ===${NC}"
echo "This image includes:"
echo "  - Ubuntu 24.04 base"
echo "  - Python 3.12 with data science stack"
echo "  - Node.js 18.x with document processing tools"
echo "  - Document processing tools (pandoc, libreoffice, etc.)"
echo "  - Skills directory with PDF, DOCX, PPTX, XLSX processing guides"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Step 1: Copy skills directory to build context
echo -e "${YELLOW}Step 1: Copying skills directory to build context...${NC}"
REFERENCE_SKILLS="../../../reference/environment_reference/skills"
BUILD_SKILLS="./skills"

if [ -d "$REFERENCE_SKILLS" ]; then
    # Remove old skills directory if it exists
    if [ -d "$BUILD_SKILLS" ]; then
        echo "  Removing old skills directory..."
        rm -rf "$BUILD_SKILLS"
    fi

    # Copy skills directory
    echo "  Copying skills from $REFERENCE_SKILLS..."
    cp -r "$REFERENCE_SKILLS" "$BUILD_SKILLS"
    echo -e "${GREEN}  ✓ Skills directory copied${NC}"
else
    echo -e "${YELLOW}  ⚠ Skills directory not found at $REFERENCE_SKILLS${NC}"
    echo "  Creating empty skills structure..."
    mkdir -p "$BUILD_SKILLS/public/docx"
    mkdir -p "$BUILD_SKILLS/public/pdf"
    mkdir -p "$BUILD_SKILLS/public/pptx"
    mkdir -p "$BUILD_SKILLS/public/xlsx"
fi

# Step 2: Build the Docker image
echo -e "${YELLOW}Step 2: Building Docker image...${NC}"
echo "  This may take several minutes as it installs many packages..."

# Build with progress output
if docker build -t claude-agent:latest -f Dockerfile.agent . ; then
    echo -e "${GREEN}  ✓ Docker image built successfully${NC}"
else
    echo -e "${RED}  ✗ Docker build failed${NC}"
    exit 1
fi

# Step 3: Clean up temporary files
echo -e "${YELLOW}Step 3: Cleaning up...${NC}"
if [ -d "$BUILD_SKILLS" ]; then
    echo "  Removing temporary skills directory..."
    rm -rf "$BUILD_SKILLS"
fi
echo -e "${GREEN}  ✓ Cleanup complete${NC}"

# Step 4: Display image info
echo -e "${YELLOW}Step 4: Image information${NC}"
IMAGE_SIZE=$(docker images claude-agent:latest --format "{{.Size}}")
IMAGE_ID=$(docker images claude-agent:latest --format "{{.ID}}")

echo "  Image: claude-agent:latest"
echo "  ID: $IMAGE_ID"
echo "  Size: $IMAGE_SIZE"
echo ""

# Step 5: Quick test
echo -e "${YELLOW}Step 5: Quick test${NC}"
echo "  Running a quick test command..."

if docker run --rm claude-agent:latest bash -c "python3 --version && node --version && pandoc --version | head -1"; then
    echo -e "${GREEN}  ✓ Basic tools verified${NC}"
else
    echo -e "${RED}  ✗ Basic tools test failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}=== Build Complete ===${NC}"
echo "The claude-agent:latest image is ready for use."
echo ""
echo "To test the image interactively:"
echo "  docker run -it --rm -v ./test-workspace:/mnt claude-agent:latest"
echo ""
echo "The image includes:"
echo "  - ${GREEN}✓${NC} Python 3.12 with 100+ packages (numpy, pandas, scikit-learn, etc.)"
echo "  - ${GREEN}✓${NC} Node.js 18.x with document tools (docx, pptxgenjs, pdf-lib, etc.)"
echo "  - ${GREEN}✓${NC} System tools (pandoc, libreoffice, imagemagick, tesseract, etc.)"
echo "  - ${GREEN}✓${NC} Skills directory at /mnt/skills with processing guides"
echo "  - ${GREEN}✓${NC} Writable /mnt directory for agent workspace"