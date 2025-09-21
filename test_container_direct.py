#!/usr/bin/env python3
"""
Direct test of container startup to debug issues.
"""

import docker
import os
import platform
import tempfile
import time
from pathlib import Path

# Connect to Docker
if platform.system() == 'Darwin':
    socket_path = os.path.expanduser('~/.docker/run/docker.sock')
    if os.path.exists(socket_path):
        docker_client = docker.DockerClient(base_url=f'unix://{socket_path}')
    else:
        docker_client = docker.from_env()
else:
    docker_client = docker.from_env()

print("Testing container startup...")

# Create a temporary working directory
work_dir = Path("./test-container-work")
work_dir.mkdir(exist_ok=True)

try:
    # Create test container
    config = {
        "image": "claude-agent:latest",
        "name": "test-direct-container",
        "hostname": "agent-test",
        "network_mode": "host",
        "volumes": {
            str(work_dir.absolute()): {
                "bind": "/mnt",
                "mode": "rw"
            }
        },
        "environment": {
            "AGENT_ID": "test",
            "DEBIAN_FRONTEND": "noninteractive"
        },
        "working_dir": "/mnt",
        "user": "agent",
        "read_only": True,
        "tmpfs": {
            "/tmp": "size=512M",
            "/var/tmp": "size=512M",
            "/home/agent/.cache": "size=256M"
        },
        "cap_add": [
            "CHOWN",
            "DAC_OVERRIDE",
            "SETGID",
            "SETUID",
            "NET_RAW",
            "NET_BIND_SERVICE"
        ],
        "cap_drop": ["ALL"],
        "security_opt": ["no-new-privileges"],
        "command": "tail -f /dev/null",
        "detach": True,
        "stdin_open": True,
        "tty": True
    }

    print(f"Creating container with config...")
    container = docker_client.containers.run(**config)

    # Wait for container
    time.sleep(2)
    container.reload()

    print(f"Container status: {container.status}")

    if container.status == "running":
        print("✓ Container started successfully!")

        # Test command execution
        exit_code, output = container.exec_run("echo 'Hello from container!'")
        print(f"Test command output: {output.decode('utf-8').strip()}")

        # Check mounts
        exit_code, output = container.exec_run("ls -la /mnt")
        print(f"Mount check:\n{output.decode('utf-8')}")

    else:
        print(f"✗ Container failed to start. Status: {container.status}")
        # Get logs
        logs = container.logs().decode('utf-8')
        print(f"Container logs:\n{logs}")

    # Cleanup
    container.stop()
    container.remove()
    print("Container cleaned up.")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

    # Try to cleanup
    try:
        for container in docker_client.containers.list(all=True):
            if container.name == "test-direct-container":
                container.stop()
                container.remove()
    except:
        pass