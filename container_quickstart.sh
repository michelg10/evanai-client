#!/bin/bash

# Container Quick Start Script
# Easy access to container debugging and testing

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}============================================${NC}"
echo -e "${GREEN}EvanAI Container Shell - Quick Start${NC}"
echo -e "${CYAN}============================================${NC}"
echo

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Check if image exists
if ! docker images | grep -q "claude-agent"; then
    echo -e "${YELLOW}Claude agent image not found. Building...${NC}"
    cd evanai_client/tools/linux_desktop_environment/scripts
    ./build-agent-image.sh
    cd -
fi

# Show options
echo -e "${GREEN}Available Commands:${NC}"
echo "1. Interactive mode (browse and select containers)"
echo "2. Quick shell (create/enter a test container)"
echo "3. List all containers"
echo "4. Verify container environment"
echo "5. Test stateful shell behavior"
echo "6. Clean up all containers"
echo

read -p "Select option (1-6): " choice

case $choice in
    1)
        echo -e "${CYAN}Starting interactive mode...${NC}"
        python -m evanai_client.container_shell
        ;;
    2)
        echo -e "${CYAN}Creating/entering test container...${NC}"
        # Create a quick test container and enter it
        container_name="test-$(date +%Y%m%d-%H%M%S)"
        evanai-client shell $container_name
        ;;
    3)
        echo -e "${CYAN}Listing containers...${NC}"
        docker ps -a | grep claude-agent || echo "No containers found"
        ;;
    4)
        echo -e "${CYAN}Enter container name to verify (or press Enter for latest):${NC}"
        read container_name
        if [ -z "$container_name" ]; then
            # Get the latest container
            container_name=$(docker ps -a --format "{{.Names}}" | grep claude-agent | head -1)
            if [ -z "$container_name" ]; then
                echo -e "${RED}No containers found. Create one first.${NC}"
                exit 1
            fi
        fi
        python -c "
from evanai_client.container_shell import ContainerShell
shell = ContainerShell()
shell.verify_container('$container_name')
        "
        ;;
    5)
        echo -e "${CYAN}Enter container name to test (or press Enter for latest):${NC}"
        read container_name
        if [ -z "$container_name" ]; then
            # Get the latest container
            container_name=$(docker ps -a --format "{{.Names}}" | grep claude-agent | head -1)
            if [ -z "$container_name" ]; then
                echo -e "${RED}No containers found. Create one first.${NC}"
                exit 1
            fi
        fi
        python -c "
from evanai_client.container_shell import ContainerShell
shell = ContainerShell()
shell.run_test_sequence('$container_name')
        "
        ;;
    6)
        echo -e "${YELLOW}This will stop and remove all claude-agent containers.${NC}"
        read -p "Are you sure? (y/N): " confirm
        if [ "$confirm" = "y" ]; then
            docker rm -f $(docker ps -aq --filter name=claude-agent) 2>/dev/null || true
            echo -e "${GREEN}✓ All containers cleaned up${NC}"
        else
            echo "Cancelled"
        fi
        ;;
    *)
        echo -e "${RED}Invalid option${NC}"
        exit 1
        ;;
esac