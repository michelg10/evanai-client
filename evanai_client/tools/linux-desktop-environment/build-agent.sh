#!/bin/bash

# Claude Agent Environment Build Script
# Builds the isolated agent Docker image

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="claude-agent"
IMAGE_TAG="latest"
DOCKERFILE="Dockerfile.agent"
BUILD_CONTEXT="."
NO_CACHE=false
PUSH=false
REGISTRY=""

# Function to print colored messages
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Build the Claude agent Docker image.

OPTIONS:
    --no-cache          Build without cache
    --tag TAG           Image tag (default: latest)
    --push              Push to registry after build
    --registry REG      Registry URL (for push)
    -h, --help          Show this help

EXAMPLES:
    $0                      # Basic build
    $0 --no-cache           # Clean build
    $0 --tag v1.0 --push    # Build and push

EOF
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        --push)
            PUSH=true
            shift
            ;;
        --registry)
            REGISTRY="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            ;;
        *)
            print_message "$RED" "Unknown option: $1"
            show_usage
            ;;
    esac
done

# Check prerequisites
print_message "$BLUE" "=== Claude Agent Build ==="
print_message "$YELLOW" "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    print_message "$RED" "Error: Docker is not installed"
    exit 1
fi

if ! docker info &> /dev/null; then
    print_message "$RED" "Error: Docker daemon is not running"
    exit 1
fi

if [ ! -f "$DOCKERFILE" ]; then
    print_message "$RED" "Error: $DOCKERFILE not found"
    exit 1
fi

print_message "$GREEN" "✓ Prerequisites met"

# Create runtime directories
print_message "$YELLOW" "Creating runtime directories..."
mkdir -p evanai-runtime/agent-working-directory
print_message "$GREEN" "✓ Directories created"

# Build image
print_message "$YELLOW" "Building image: ${IMAGE_NAME}:${IMAGE_TAG}"

BUILD_CMD="docker build"
if [ "$NO_CACHE" = true ]; then
    BUILD_CMD="$BUILD_CMD --no-cache"
fi

FULL_IMAGE="${IMAGE_NAME}:${IMAGE_TAG}"
if [ -n "$REGISTRY" ]; then
    FULL_IMAGE="${REGISTRY}/${FULL_IMAGE}"
fi

BUILD_CMD="$BUILD_CMD -t $FULL_IMAGE -f $DOCKERFILE $BUILD_CONTEXT"

if $BUILD_CMD; then
    print_message "$GREEN" "✓ Build successful"
else
    print_message "$RED" "✗ Build failed"
    exit 1
fi

# Get image info
print_message "$BLUE" "\n=== Image Information ==="
docker images "$FULL_IMAGE" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

# Test the image
print_message "$YELLOW" "\nTesting image..."

# Run basic test
if docker run --rm "$FULL_IMAGE" bash -c "python3 --version && node --version" > /dev/null 2>&1; then
    print_message "$GREEN" "✓ Basic test passed"
else
    print_message "$RED" "✗ Basic test failed"
    exit 1
fi

# Test with read-only root
TEST_ID="test-$(date +%s)"
if docker run --rm --read-only \
    --tmpfs /tmp/agent:rw,noexec,nosuid \
    --tmpfs /home/agent/.cache:rw,noexec,nosuid \
    -v "./evanai-runtime/agent-working-directory/${TEST_ID}:/mnt:rw" \
    "$FULL_IMAGE" \
    bash -c "echo 'test' > /mnt/test.txt && cat /mnt/test.txt" > /dev/null 2>&1; then
    print_message "$GREEN" "✓ Read-only filesystem test passed"
    rm -rf "./evanai-runtime/agent-working-directory/${TEST_ID}"
else
    print_message "$RED" "✗ Read-only filesystem test failed"
fi

# Push if requested
if [ "$PUSH" = true ]; then
    print_message "$YELLOW" "\nPushing to registry..."
    if docker push "$FULL_IMAGE"; then
        print_message "$GREEN" "✓ Push successful"
    else
        print_message "$RED" "✗ Push failed"
        exit 1
    fi
fi

# Show usage instructions
print_message "$BLUE" "\n=== Usage Instructions ==="
echo "1. Launch agent with script:"
echo "   ./launch-agent.sh --id my-agent"
echo ""
echo "2. Use Python manager:"
echo "   python3 agent_manager.py create --id my-agent"
echo ""
echo "3. Direct Docker run:"
echo "   docker run -it --rm \\"
echo "     --read-only \\"
echo "     -v ./evanai-runtime/agent-working-directory/my-agent:/mnt \\"
echo "     $FULL_IMAGE"
echo ""
echo "4. Test with docker-compose:"
echo "   docker-compose -f docker-compose.agent.yml --profile test up test-agent"

print_message "$GREEN" "\n✓ Build complete!"