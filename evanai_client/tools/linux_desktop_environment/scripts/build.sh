#!/bin/bash

# Claude Environment Docker Build Script
# This script builds the Claude environment Docker image with various options

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="claude-environment"
IMAGE_TAG="latest"
DOCKERFILE="Dockerfile"
BUILD_CONTEXT="."
NO_CACHE=false
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --tag|-t)
            IMAGE_TAG="$2"
            shift 2
            ;;
        --name|-n)
            IMAGE_NAME="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --no-cache        Build without using cache"
            echo "  --verbose, -v     Enable verbose output"
            echo "  --tag, -t TAG     Specify image tag (default: latest)"
            echo "  --name, -n NAME   Specify image name (default: claude-environment)"
            echo "  --help, -h        Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                      # Basic build"
            echo "  $0 --no-cache           # Build without cache"
            echo "  $0 -t dev -v           # Build with 'dev' tag and verbose output"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Function to print colored messages
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    print_message "$YELLOW" "Checking prerequisites..."

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_message "$RED" "Error: Docker is not installed"
        exit 1
    fi

    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        print_message "$RED" "Error: Docker daemon is not running"
        exit 1
    fi

    # Check if Dockerfile exists
    if [ ! -f "$DOCKERFILE" ]; then
        print_message "$RED" "Error: Dockerfile not found at $DOCKERFILE"
        exit 1
    fi

    # Check if requirements.txt exists
    if [ ! -f "requirements.txt" ]; then
        print_message "$RED" "Error: requirements.txt not found"
        exit 1
    fi

    print_message "$GREEN" "✓ All prerequisites met"
}

# Function to create necessary directories
create_directories() {
    print_message "$YELLOW" "Creating necessary directories..."

    mkdir -p skills/public/{docx,pdf,pptx,xlsx}
    mkdir -p knowledge
    mkdir -p user-data/{uploads,outputs}
    mkdir -p workspace
    mkdir -p notebooks

    print_message "$GREEN" "✓ Directories created"
}

# Function to build the Docker image
build_image() {
    print_message "$YELLOW" "Building Docker image: ${IMAGE_NAME}:${IMAGE_TAG}..."

    # Prepare build command
    BUILD_CMD="docker build"

    if [ "$NO_CACHE" = true ]; then
        BUILD_CMD="$BUILD_CMD --no-cache"
    fi

    if [ "$VERBOSE" = true ]; then
        BUILD_CMD="$BUILD_CMD --progress=plain"
    fi

    BUILD_CMD="$BUILD_CMD -t ${IMAGE_NAME}:${IMAGE_TAG} -f ${DOCKERFILE} ${BUILD_CONTEXT}"

    # Execute build
    if [ "$VERBOSE" = true ]; then
        print_message "$YELLOW" "Build command: $BUILD_CMD"
    fi

    if $BUILD_CMD; then
        print_message "$GREEN" "✓ Docker image built successfully: ${IMAGE_NAME}:${IMAGE_TAG}"
    else
        print_message "$RED" "✗ Docker build failed"
        exit 1
    fi
}

# Function to verify the built image
verify_image() {
    print_message "$YELLOW" "Verifying built image..."

    # Check if image exists
    if docker image inspect "${IMAGE_NAME}:${IMAGE_TAG}" &> /dev/null; then
        print_message "$GREEN" "✓ Image exists"

        # Get image size
        IMAGE_SIZE=$(docker image inspect "${IMAGE_NAME}:${IMAGE_TAG}" --format='{{.Size}}' | numfmt --to=iec-i --suffix=B)
        print_message "$GREEN" "  Image size: $IMAGE_SIZE"

        # Run verification script inside container
        print_message "$YELLOW" "Running environment verification..."
        docker run --rm "${IMAGE_NAME}:${IMAGE_TAG}" /verify_environment.sh

    else
        print_message "$RED" "✗ Image not found"
        exit 1
    fi
}

# Function to run post-build tests
run_tests() {
    print_message "$YELLOW" "Running basic functionality tests..."

    # Test Python
    if docker run --rm "${IMAGE_NAME}:${IMAGE_TAG}" python3 -c "import numpy, pandas, sklearn; print('Python OK')"; then
        print_message "$GREEN" "✓ Python packages work"
    else
        print_message "$RED" "✗ Python test failed"
    fi

    # Test Node
    if docker run --rm "${IMAGE_NAME}:${IMAGE_TAG}" node -e "console.log('Node OK')"; then
        print_message "$GREEN" "✓ Node.js works"
    else
        print_message "$RED" "✗ Node.js test failed"
    fi

    # Test document tools
    if docker run --rm "${IMAGE_NAME}:${IMAGE_TAG}" pandoc --version &> /dev/null; then
        print_message "$GREEN" "✓ Pandoc works"
    else
        print_message "$RED" "✗ Pandoc test failed"
    fi
}

# Function to show next steps
show_next_steps() {
    print_message "$YELLOW" "\n=== Next Steps ==="
    echo "1. Run the container interactively:"
    echo "   docker run -it --rm ${IMAGE_NAME}:${IMAGE_TAG}"
    echo ""
    echo "2. Run with docker-compose:"
    echo "   docker-compose up -d"
    echo ""
    echo "3. Run with volumes:"
    echo "   docker run -it --rm \\"
    echo "     -v \$(pwd)/workspace:/home/claude/workspace \\"
    echo "     -v \$(pwd)/skills:/mnt/skills \\"
    echo "     ${IMAGE_NAME}:${IMAGE_TAG}"
    echo ""
    echo "4. Run Jupyter notebook:"
    echo "   docker-compose --profile jupyter up jupyter"
    echo ""
}

# Main execution
main() {
    print_message "$GREEN" "=== Claude Environment Docker Build Script ==="
    echo ""

    # Run build steps
    check_prerequisites
    create_directories
    build_image
    verify_image
    run_tests

    print_message "$GREEN" "\n✓ Build completed successfully!"
    show_next_steps
}

# Run main function
main