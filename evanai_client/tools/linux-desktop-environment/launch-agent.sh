#!/bin/bash

# Agent Container Launcher
# Launches isolated agent environments with ID-based working directories

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="claude-agent:latest"
RUNTIME_BASE_DIR="${EVANAI_RUNTIME_DIR:-./evanai-runtime}"
WORKING_DIR_BASE="$RUNTIME_BASE_DIR/agent-working-directory"
CONTAINER_PREFIX="claude-agent"
# No isolated network - using host network

# Default settings
MEMORY_LIMIT="2g"
CPU_LIMIT="2"
READONLY_ROOT=true
REMOVE_ON_EXIT=false
INTERACTIVE=false
DETACHED=false

# Function to print colored messages
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to generate unique agent ID
generate_agent_id() {
    echo "$(date +%Y%m%d-%H%M%S)-$(openssl rand -hex 4)"
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS] [COMMAND]

Launch an isolated Claude agent environment with ID-based working directory.

OPTIONS:
    -i, --id ID              Specify agent ID (auto-generated if not provided)
    -m, --memory LIMIT       Memory limit (default: 2g)
    -c, --cpu LIMIT         CPU limit (default: 2)
    --interactive           Run interactively with TTY
    -d, --detached          Run in background
    --rm                    Remove container on exit
    --no-readonly           Disable read-only root filesystem
    --runtime-dir DIR       Base directory for runtime data
    -h, --help              Show this help message

COMMAND:
    Command to execute in the agent environment (default: /bin/bash)

EXAMPLES:
    $0 --id agent-001 --interactive          # Interactive session with specific ID
    $0 -d --rm python3 /mnt/script.py        # Run script in background
    $0 --memory 4g --cpu 4                   # Launch with more resources

ENVIRONMENT VARIABLES:
    EVANAI_RUNTIME_DIR      Base directory for agent runtime data
    AGENT_NETWORK          Docker network name for agents

EOF
    exit 0
}

# Parse command line arguments
AGENT_ID=""
COMMAND=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--id)
            AGENT_ID="$2"
            shift 2
            ;;
        -m|--memory)
            MEMORY_LIMIT="$2"
            shift 2
            ;;
        -c|--cpu)
            CPU_LIMIT="$2"
            shift 2
            ;;
        --interactive)
            INTERACTIVE=true
            shift
            ;;
        -d|--detached)
            DETACHED=true
            shift
            ;;
        --rm)
            REMOVE_ON_EXIT=true
            shift
            ;;
        --no-readonly)
            READONLY_ROOT=false
            shift
            ;;
        --runtime-dir)
            RUNTIME_BASE_DIR="$2"
            WORKING_DIR_BASE="$2/agent-working-directory"
            shift 2
            ;;
        -h|--help)
            show_usage
            ;;
        *)
            # Remaining arguments are the command
            COMMAND="$@"
            break
            ;;
    esac
done

# Generate agent ID if not provided
if [ -z "$AGENT_ID" ]; then
    AGENT_ID=$(generate_agent_id)
    print_message "$YELLOW" "Generated Agent ID: $AGENT_ID"
fi

# Validate agent ID (alphanumeric, dash, underscore only)
if ! [[ "$AGENT_ID" =~ ^[a-zA-Z0-9_-]+$ ]]; then
    print_message "$RED" "Error: Invalid agent ID. Use only alphanumeric characters, dashes, and underscores."
    exit 1
fi

# Setup paths
AGENT_WORK_DIR="$WORKING_DIR_BASE/$AGENT_ID"
CONTAINER_NAME="${CONTAINER_PREFIX}-${AGENT_ID}"

# Check if container already exists
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    print_message "$RED" "Error: Container $CONTAINER_NAME already exists"
    print_message "$YELLOW" "Remove it with: docker rm -f $CONTAINER_NAME"
    exit 1
fi

# Create working directory
print_message "$YELLOW" "Creating working directory: $AGENT_WORK_DIR"
mkdir -p "$AGENT_WORK_DIR"

# Build Docker run command
DOCKER_CMD="docker run"

# Add name and use host network
DOCKER_CMD="$DOCKER_CMD --name $CONTAINER_NAME"
DOCKER_CMD="$DOCKER_CMD --network host"

# Add resource limits
DOCKER_CMD="$DOCKER_CMD --memory $MEMORY_LIMIT"
DOCKER_CMD="$DOCKER_CMD --cpus $CPU_LIMIT"

# Add environment variables
DOCKER_CMD="$DOCKER_CMD -e AGENT_ID=$AGENT_ID"
DOCKER_CMD="$DOCKER_CMD -e AGENT_WORK_DIR=/mnt"

# Mount working directory
DOCKER_CMD="$DOCKER_CMD -v $(realpath $AGENT_WORK_DIR):/mnt"

# Add read-only root filesystem if enabled
if [ "$READONLY_ROOT" = true ]; then
    DOCKER_CMD="$DOCKER_CMD --read-only"
    # Add writable temp directory
    DOCKER_CMD="$DOCKER_CMD --tmpfs /tmp/agent:rw,noexec,nosuid,size=100m"
    DOCKER_CMD="$DOCKER_CMD --tmpfs /home/agent/.cache:rw,noexec,nosuid,size=50m"
fi

# Add security options
DOCKER_CMD="$DOCKER_CMD --security-opt no-new-privileges"
DOCKER_CMD="$DOCKER_CMD --cap-drop ALL"
# Add minimal capabilities needed for basic operations
DOCKER_CMD="$DOCKER_CMD --cap-add CHOWN"
DOCKER_CMD="$DOCKER_CMD --cap-add DAC_OVERRIDE"
DOCKER_CMD="$DOCKER_CMD --cap-add SETGID"
DOCKER_CMD="$DOCKER_CMD --cap-add SETUID"

# Set resource limits via ulimits
DOCKER_CMD="$DOCKER_CMD --ulimit nofile=1024:2048"
DOCKER_CMD="$DOCKER_CMD --ulimit nproc=512:1024"

# Add interactive/detached flags
if [ "$INTERACTIVE" = true ]; then
    DOCKER_CMD="$DOCKER_CMD -it"
fi

if [ "$DETACHED" = true ]; then
    DOCKER_CMD="$DOCKER_CMD -d"
fi

if [ "$REMOVE_ON_EXIT" = true ]; then
    DOCKER_CMD="$DOCKER_CMD --rm"
fi

# Add the image
DOCKER_CMD="$DOCKER_CMD $IMAGE_NAME"

# Add command if provided
if [ -n "$COMMAND" ]; then
    DOCKER_CMD="$DOCKER_CMD $COMMAND"
fi

# Show configuration
print_message "$BLUE" "=== Agent Configuration ==="
echo "Agent ID:        $AGENT_ID"
echo "Container Name:  $CONTAINER_NAME"
echo "Working Dir:     $AGENT_WORK_DIR"
echo "Memory Limit:    $MEMORY_LIMIT"
echo "CPU Limit:       $CPU_LIMIT"
echo "Read-only Root:  $READONLY_ROOT"
echo "Network:         host (full network access)"

if [ -n "$COMMAND" ]; then
    echo "Command:         $COMMAND"
fi

print_message "$BLUE" "========================="
echo ""

# Launch container
print_message "$GREEN" "Launching agent container..."

if [ "$INTERACTIVE" = false ] && [ "$DETACHED" = false ]; then
    # Default to interactive if neither flag is set and no command provided
    if [ -z "$COMMAND" ]; then
        DOCKER_CMD="$DOCKER_CMD -it"
    fi
fi

# Execute Docker command
eval $DOCKER_CMD

# Show status
if [ "$DETACHED" = true ]; then
    print_message "$GREEN" "✓ Agent container started in background"
    echo ""
    echo "View logs:    docker logs -f $CONTAINER_NAME"
    echo "Attach:       docker attach $CONTAINER_NAME"
    echo "Execute:      docker exec -it $CONTAINER_NAME bash"
    echo "Stop:         docker stop $CONTAINER_NAME"
    echo "Remove:       docker rm $CONTAINER_NAME"
else
    print_message "$GREEN" "✓ Agent container session ended"
fi

# Show working directory info
echo ""
print_message "$YELLOW" "Working directory preserved at: $AGENT_WORK_DIR"