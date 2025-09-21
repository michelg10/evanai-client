#!/bin/bash

# Claude Environment Verification Script
# This script verifies that the Docker environment is properly set up

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="${1:-claude-environment:latest}"
CONTAINER_NAME="claude-verify-$$"
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [IMAGE_NAME] [OPTIONS]"
            echo ""
            echo "Verify the Claude environment Docker image"
            echo ""
            echo "Options:"
            echo "  --verbose, -v     Enable verbose output"
            echo "  --help, -h        Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                           # Verify default image"
            echo "  $0 my-image:tag             # Verify specific image"
            echo "  $0 --verbose                # Verbose verification"
            exit 0
            ;;
        *)
            if [[ ! "$1" =~ ^-- ]]; then
                IMAGE_NAME="$1"
            fi
            shift
            ;;
    esac
done

# Function to print colored messages
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to run command in container
run_in_container() {
    local cmd=$1
    docker exec "$CONTAINER_NAME" bash -c "$cmd" 2>/dev/null || echo "Failed"
}

# Function to check if command succeeds in container
check_command() {
    local cmd=$1
    local description=$2

    if docker exec "$CONTAINER_NAME" bash -c "$cmd" &>/dev/null; then
        print_message "$GREEN" "  ✓ $description"
        return 0
    else
        print_message "$RED" "  ✗ $description"
        return 1
    fi
}

# Start verification
print_message "$BLUE" "=== Claude Environment Verification ==="
print_message "$YELLOW" "Image: $IMAGE_NAME"
echo ""

# Check if image exists
if ! docker image inspect "$IMAGE_NAME" &>/dev/null; then
    print_message "$RED" "Error: Image $IMAGE_NAME not found"
    print_message "$YELLOW" "Please build the image first using: ./build.sh"
    exit 1
fi

# Start container
print_message "$YELLOW" "Starting verification container..."
docker run -d --name "$CONTAINER_NAME" "$IMAGE_NAME" tail -f /dev/null &>/dev/null

# Ensure container is removed on exit
trap "docker rm -f $CONTAINER_NAME &>/dev/null" EXIT

# Wait for container to be ready
sleep 2

# System Information
print_message "$BLUE" "\n1. System Information"
OS_INFO=$(run_in_container "lsb_release -d 2>/dev/null | cut -f2 || cat /etc/os-release | grep PRETTY_NAME | cut -d'\"' -f2")
KERNEL=$(run_in_container "uname -r")
ARCH=$(run_in_container "uname -m")
print_message "$GREEN" "  OS: $OS_INFO"
print_message "$GREEN" "  Kernel: $KERNEL"
print_message "$GREEN" "  Architecture: $ARCH"

# Core Tools
print_message "$BLUE" "\n2. Core Tools"
PYTHON_VERSION=$(run_in_container "python3 --version 2>&1 | cut -d' ' -f2")
NODE_VERSION=$(run_in_container "node --version 2>&1")
NPM_VERSION=$(run_in_container "npm --version 2>&1")
JAVA_VERSION=$(run_in_container "java --version 2>&1 | head -1 | cut -d'\"' -f2")
GCC_VERSION=$(run_in_container "gcc --version 2>&1 | head -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1")

print_message "$GREEN" "  Python: $PYTHON_VERSION (expected: 3.12.x)"
print_message "$GREEN" "  Node: $NODE_VERSION (expected: v18.x)"
print_message "$GREEN" "  NPM: $NPM_VERSION"
print_message "$GREEN" "  Java: $JAVA_VERSION (expected: 21.x)"
print_message "$GREEN" "  GCC: $GCC_VERSION"

# Python Packages
print_message "$BLUE" "\n3. Python Package Verification"
CRITICAL_PACKAGES=(
    "numpy"
    "pandas"
    "scipy"
    "scikit-learn"
    "matplotlib"
    "flask"
    "fastapi"
    "jupyter"
    "opencv-python:cv2"
    "PIL"
    "requests"
    "beautifulsoup4:bs4"
    "pypdf"
    "markitdown"
)

for package in "${CRITICAL_PACKAGES[@]}"; do
    if [[ "$package" == *":"* ]]; then
        pkg_name="${package%%:*}"
        import_name="${package##*:}"
    else
        pkg_name="$package"
        import_name="$package"
    fi

    check_command "python3 -c 'import ${import_name}'" "$pkg_name"
done

TOTAL_PY_PACKAGES=$(run_in_container "pip list 2>/dev/null | tail -n +3 | wc -l")
print_message "$GREEN" "  Total Python packages: $TOTAL_PY_PACKAGES"

# NPM Packages
print_message "$BLUE" "\n4. NPM Package Verification"
CRITICAL_NPM_PACKAGES=(
    "typescript"
    "playwright"
    "@mermaid-js/mermaid-cli"
    "marked"
    "react"
    "pdf-lib"
)

for package in "${CRITICAL_NPM_PACKAGES[@]}"; do
    check_command "npm list -g $package 2>/dev/null | grep -q $package" "$package"
done

TOTAL_NPM_PACKAGES=$(run_in_container "npm list -g --depth=0 2>/dev/null | grep -c '^├─\|^└─' || echo '0'")
print_message "$GREEN" "  Total NPM packages: $TOTAL_NPM_PACKAGES"

# Document Processing Tools
print_message "$BLUE" "\n5. Document Processing Tools"
check_command "pandoc --version" "Pandoc"
check_command "convert --version" "ImageMagick"
check_command "pdflatex --version" "LaTeX"
check_command "soffice --version" "LibreOffice"
check_command "tesseract --version" "Tesseract OCR"
check_command "ffmpeg -version" "FFmpeg"

# Directory Structure
print_message "$BLUE" "\n6. Directory Structure"
DIRS_TO_CHECK=(
    "/home/claude"
    "/home/claude/.npm-global"
    "/mnt/user-data"
    "/mnt/skills"
    "/mnt/knowledge"
    "/opt/pw-browsers"
)

for dir in "${DIRS_TO_CHECK[@]}"; do
    check_command "test -d $dir" "$dir"
done

# Environment Variables
print_message "$BLUE" "\n7. Environment Variables"
ENV_VARS_TO_CHECK=(
    "PYTHONUNBUFFERED"
    "IS_SANDBOX"
    "JAVA_HOME"
    "NODE_PATH"
    "NPM_CONFIG_PREFIX"
)

for var in "${ENV_VARS_TO_CHECK[@]}"; do
    VALUE=$(run_in_container "echo \$$var")
    if [ "$VALUE" != "" ] && [ "$VALUE" != "Failed" ]; then
        print_message "$GREEN" "  ✓ $var=$VALUE"
    else
        print_message "$RED" "  ✗ $var not set"
    fi
done

# Functional Tests
print_message "$BLUE" "\n8. Functional Tests"

# Test Python data processing
check_command "python3 -c 'import pandas as pd; df = pd.DataFrame({\"a\": [1, 2, 3]}); print(df.sum())'" \
    "Python data processing"

# Test document conversion
check_command "echo '# Test' | pandoc -f markdown -t html" \
    "Pandoc markdown conversion"

# Test Node.js
check_command "node -e 'console.log(1 + 1)'" \
    "Node.js execution"

# Test TypeScript
check_command "echo 'const x: number = 1;' | npx tsc --stdin --noEmit" \
    "TypeScript compilation"

# Package Counts Summary
print_message "$BLUE" "\n9. Package Summary"
DPKG_COUNT=$(run_in_container "dpkg -l 2>/dev/null | grep -c '^ii' || echo '0'")
print_message "$GREEN" "  System packages (dpkg): $DPKG_COUNT"
print_message "$GREEN" "  Python packages: $TOTAL_PY_PACKAGES"
print_message "$GREEN" "  NPM packages: $TOTAL_NPM_PACKAGES"

# Performance Tests (optional)
if [ "$VERBOSE" = true ]; then
    print_message "$BLUE" "\n10. Performance Tests"

    # Test NumPy performance
    NUMPY_TIME=$(run_in_container "python3 -c 'import time, numpy as np; start=time.time(); np.random.rand(1000, 1000).dot(np.random.rand(1000, 1000)); print(f\"{time.time()-start:.2f}s\")'")
    print_message "$GREEN" "  NumPy matrix multiplication (1000x1000): $NUMPY_TIME"

    # Test pandas performance
    PANDAS_TIME=$(run_in_container "python3 -c 'import time, pandas as pd; start=time.time(); pd.DataFrame({\"a\": range(1000000)}).groupby(lambda x: x % 100).sum(); print(f\"{time.time()-start:.2f}s\")'")
    print_message "$GREEN" "  Pandas groupby (1M rows): $PANDAS_TIME"
fi

# Final Summary
print_message "$BLUE" "\n=== Verification Summary ==="

# Count successes and failures
SUCCESS_COUNT=$(grep -c "✓" <<< "$(docker logs $CONTAINER_NAME 2>&1)" || echo 0)
FAILURE_COUNT=$(grep -c "✗" <<< "$(docker logs $CONTAINER_NAME 2>&1)" || echo 0)

if [ "$FAILURE_COUNT" -eq 0 ]; then
    print_message "$GREEN" "✓ All verification checks passed!"
    print_message "$GREEN" "The Claude environment is properly configured."
else
    print_message "$YELLOW" "⚠ Some verification checks failed"
    print_message "$YELLOW" "The environment may still work but some features might be limited."
fi

print_message "$BLUE" "\nTo run the environment:"
print_message "$NC" "  docker run -it --rm $IMAGE_NAME"