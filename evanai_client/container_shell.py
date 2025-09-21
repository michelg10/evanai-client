#!/usr/bin/env python3
"""
Interactive Container Shell for EvanAI Linux Environment

Provides easy access to Docker containers for debugging, testing, and verification.
"""

import os
import sys
import subprocess
import click
import docker
from typing import List, Optional, Dict, Any
from datetime import datetime
from colorama import init, Fore, Style
from pathlib import Path

init(autoreset=True)

class ContainerShell:
    """Interactive shell interface for container management and debugging."""

    def __init__(self):
        try:
            # Try standard location first
            self.docker_client = docker.from_env()
        except docker.errors.DockerException:
            # Try macOS Docker Desktop location
            try:
                import platform
                if platform.system() == "Darwin":
                    # Check for Docker Desktop socket
                    docker_socket = os.path.expanduser("~/.docker/run/docker.sock")
                    if os.path.exists(docker_socket):
                        self.docker_client = docker.DockerClient(base_url=f"unix://{docker_socket}")
                    else:
                        raise docker.errors.DockerException("Docker socket not found")
                else:
                    raise
            except docker.errors.DockerException as e:
                print(f"{Fore.RED}Error: Cannot connect to Docker. Is Docker running?{Style.RESET_ALL}")
                print(f"Details: {e}")
                sys.exit(1)

        self.container_prefix = "claude-agent-"
        self.image_name = "claude-agent:latest"

    def list_containers(self, all_containers: bool = False) -> List[Dict[str, Any]]:
        """List all claude-agent containers."""
        containers = []
        for container in self.docker_client.containers.list(all=all_containers):
            if container.name.startswith(self.container_prefix):
                info = {
                    'name': container.name,
                    'id': container.short_id,
                    'status': container.status,
                    'created': container.attrs['Created'],
                    'conversation_id': container.name.replace(self.container_prefix, ''),
                }
                containers.append(info)
        return containers

    def print_containers(self, all_containers: bool = False):
        """Print a formatted list of containers."""
        containers = self.list_containers(all_containers)

        if not containers:
            print(f"{Fore.YELLOW}No containers found. Start a debug session or use 'create' command.{Style.RESET_ALL}")
            return

        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Claude Agent Containers{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

        for i, container in enumerate(containers, 1):
            status_color = Fore.GREEN if container['status'] == 'running' else Fore.YELLOW
            print(f"{i}. {Fore.CYAN}{container['name']}{Style.RESET_ALL}")
            print(f"   Status: {status_color}{container['status']}{Style.RESET_ALL}")
            print(f"   ID: {container['id']}")
            print(f"   Conversation: {container['conversation_id']}")
            print()

    def create_container(self, conversation_id: Optional[str] = None) -> str:
        """Create a new container."""
        if not conversation_id:
            conversation_id = f"manual-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        container_name = f"{self.container_prefix}{conversation_id}"

        # Check if container already exists
        try:
            existing = self.docker_client.containers.get(container_name)
            print(f"{Fore.YELLOW}Container {container_name} already exists.{Style.RESET_ALL}")
            if existing.status != 'running':
                print(f"{Fore.CYAN}Starting container...{Style.RESET_ALL}")
                existing.start()
            return container_name
        except docker.errors.NotFound:
            pass

        print(f"{Fore.CYAN}Creating new container: {container_name}{Style.RESET_ALL}")

        # Check if image exists
        try:
            self.docker_client.images.get(self.image_name)
        except docker.errors.ImageNotFound:
            print(f"{Fore.RED}Image {self.image_name} not found!{Style.RESET_ALL}")
            print(f"Run: cd evanai_client/tools/linux_desktop_environment/scripts && ./build-agent-image.sh")
            sys.exit(1)

        # Create container with same settings as lazy_agent_manager
        container = self.docker_client.containers.run(
            self.image_name,
            name=container_name,
            detach=True,
            stdin_open=True,
            tty=True,
            network_mode="host",
            volumes={
                f"/tmp/{container_name}": {
                    'bind': '/mnt',
                    'mode': 'rw'
                }
            },
            environment={
                "AGENT_ID": conversation_id,
                "IS_MANUAL": "1"
            },
            mem_limit="2g",
            cpu_quota=200000,  # 2 CPUs
            remove=False,
            command="/bin/bash"
        )

        print(f"{Fore.GREEN}✓ Container created: {container_name}{Style.RESET_ALL}")
        return container_name

    def shell_into_container(self, container_name: str):
        """Open an interactive shell in the container."""
        print(f"{Fore.CYAN}Entering container: {container_name}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Type 'exit' to leave the container shell{Style.RESET_ALL}\n")

        # Use subprocess for interactive shell
        cmd = ["docker", "exec", "-it", container_name, "bash"]
        subprocess.run(cmd)

    def execute_command(self, container_name: str, command: str) -> tuple:
        """Execute a single command in the container."""
        try:
            container = self.docker_client.containers.get(container_name)
            # Wrap command in bash -c for proper shell handling
            bash_command = ["bash", "-c", command]
            result = container.exec_run(bash_command, stdout=True, stderr=True, user="agent")
            return result.exit_code, result.output.decode('utf-8', errors='replace')
        except Exception as e:
            return 1, str(e)

    def verify_container(self, container_name: str):
        """Run verification checks on the container."""
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Container Verification: {container_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")

        checks = [
            ("System Info", "uname -a"),
            ("User Info", "whoami && pwd"),
            ("Python Version", "python3 --version"),
            ("Node Version", "node --version 2>/dev/null || echo 'Node not installed'"),
            ("Working Directory", "ls -la /mnt"),
            ("Skills Directory", "ls -la /mnt/skills/public 2>/dev/null || echo 'Skills not found'"),
            ("Skills Count", "find /mnt/skills -type f 2>/dev/null | wc -l || echo '0'"),
            ("Writable Check", "touch /mnt/test_write && rm /mnt/test_write && echo 'Writable' || echo 'Not writable'"),
            ("Environment", "env | grep -E '^(AGENT_ID|PATH|HOME|USER)' | head -5"),
            ("Disk Space", "df -h /mnt"),
            ("Memory", "free -h"),
            ("Processes", "ps aux | head -5"),
        ]

        for check_name, command in checks:
            print(f"{Fore.YELLOW}{check_name}:{Style.RESET_ALL}")
            exit_code, output = self.execute_command(container_name, command)
            if exit_code == 0:
                print(f"{Fore.GREEN}✓{Style.RESET_ALL} {output.strip()}")
            else:
                print(f"{Fore.RED}✗{Style.RESET_ALL} {output.strip()}")
            print()

    def inspect_skills(self, container_name: str):
        """Inspect skills directory in detail."""
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Skills Inspection: {container_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")

        # Check skills structure
        _, output = self.execute_command(container_name, "find /mnt/skills -type d 2>/dev/null | head -20")
        print(f"{Fore.YELLOW}Skills Directory Structure:{Style.RESET_ALL}")
        print(output)

        # Count files by type
        categories = ['pdf', 'docx', 'pptx', 'xlsx']
        print(f"{Fore.YELLOW}Files by Category:{Style.RESET_ALL}")
        for cat in categories:
            _, count = self.execute_command(container_name, f"find /mnt/skills/public/{cat} -type f 2>/dev/null | wc -l")
            print(f"  {cat}: {count.strip()} files")

        # Show some example files
        print(f"\n{Fore.YELLOW}Example Skill Files:{Style.RESET_ALL}")
        _, files = self.execute_command(container_name, "find /mnt/skills -name '*.py' -o -name '*.md' 2>/dev/null | head -10")
        print(files)

        # Check if skills are readable
        _, readable = self.execute_command(container_name, "test -r /mnt/skills && echo 'Skills readable' || echo 'Skills not readable'")
        print(f"\n{Fore.YELLOW}Access Check:{Style.RESET_ALL} {readable.strip()}")

    def run_test_sequence(self, container_name: str):
        """Run a test sequence of commands to verify stateful shell."""
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Testing Stateful Shell Behavior{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")

        test_commands = [
            ("Initial directory", "pwd"),
            ("Change to /tmp", "cd /tmp"),
            ("Verify directory change", "pwd"),
            ("Create test variable", "export TEST_VAR='Hello from container'"),
            ("Check variable", "echo $TEST_VAR"),
            ("Create alias", "alias ll='ls -la'"),
            ("Use alias", "alias | grep ll"),
            ("Create test file", "echo 'test content' > /mnt/test.txt"),
            ("Read test file", "cat /mnt/test.txt"),
            ("Cleanup", "rm -f /mnt/test.txt"),
        ]

        for description, command in test_commands:
            print(f"{Fore.YELLOW}{description}:{Style.RESET_ALL}")
            print(f"  Command: {command}")
            exit_code, output = self.execute_command(container_name, f"bash -c '{command}'")
            if exit_code == 0:
                print(f"  {Fore.GREEN}✓ Output:{Style.RESET_ALL} {output.strip()}")
            else:
                print(f"  {Fore.RED}✗ Error:{Style.RESET_ALL} {output.strip()}")
            print()

    def cleanup_container(self, container_name: str, force: bool = False):
        """Stop and optionally remove a container."""
        try:
            container = self.docker_client.containers.get(container_name)

            if container.status == 'running':
                print(f"{Fore.YELLOW}Stopping container: {container_name}{Style.RESET_ALL}")
                container.stop()

            if force:
                print(f"{Fore.YELLOW}Removing container: {container_name}{Style.RESET_ALL}")
                container.remove()
                print(f"{Fore.GREEN}✓ Container removed{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}✓ Container stopped (use --force to remove){Style.RESET_ALL}")

        except docker.errors.NotFound:
            print(f"{Fore.RED}Container not found: {container_name}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")

    def interactive_mode(self):
        """Enter interactive mode for container selection."""
        while True:
            containers = self.list_containers()

            print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}Container Shell - Interactive Mode{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")

            print("Available containers:")
            for i, container in enumerate(containers, 1):
                status_color = Fore.GREEN if container['status'] == 'running' else Fore.YELLOW
                print(f"  {i}. {container['name']} ({status_color}{container['status']}{Style.RESET_ALL})")

            print(f"\n  {len(containers) + 1}. Create new container")
            print(f"  q. Quit")

            choice = input(f"\n{Fore.CYAN}Select container (1-{len(containers) + 1}) or 'q': {Style.RESET_ALL}").strip()

            if choice.lower() == 'q':
                break

            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(containers):
                    container = containers[choice_num - 1]
                    self.container_menu(container['name'])
                elif choice_num == len(containers) + 1:
                    name = self.create_container()
                    self.container_menu(name)
                else:
                    print(f"{Fore.RED}Invalid choice{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}Invalid input{Style.RESET_ALL}")

    def container_menu(self, container_name: str):
        """Show menu for a specific container."""
        while True:
            print(f"\n{Fore.CYAN}Container: {container_name}{Style.RESET_ALL}")
            print("1. Enter shell")
            print("2. Run verification")
            print("3. Inspect skills")
            print("4. Test stateful shell")
            print("5. Execute custom command")
            print("6. Stop container")
            print("7. Back to container list")

            choice = input(f"\n{Fore.CYAN}Select action (1-7): {Style.RESET_ALL}").strip()

            if choice == '1':
                self.shell_into_container(container_name)
            elif choice == '2':
                self.verify_container(container_name)
            elif choice == '3':
                self.inspect_skills(container_name)
            elif choice == '4':
                self.run_test_sequence(container_name)
            elif choice == '5':
                cmd = input(f"{Fore.CYAN}Enter command: {Style.RESET_ALL}")
                exit_code, output = self.execute_command(container_name, cmd)
                print(f"Exit code: {exit_code}")
                print(f"Output: {output}")
            elif choice == '6':
                self.cleanup_container(container_name)
                break
            elif choice == '7':
                break
            else:
                print(f"{Fore.RED}Invalid choice{Style.RESET_ALL}")


@click.group()
def cli():
    """Container Shell - Interactive interface for EvanAI containers."""
    pass


@cli.command()
@click.option('--all', is_flag=True, help='Show all containers including stopped ones')
def list(all):
    """List all claude-agent containers."""
    shell = ContainerShell()
    shell.print_containers(all_containers=all)


@cli.command()
@click.argument('conversation_id', required=False)
def create(conversation_id):
    """Create a new container."""
    shell = ContainerShell()
    name = shell.create_container(conversation_id)
    print(f"\nContainer ready. Use 'shell {name}' to enter it.")


@cli.command()
@click.argument('container_name', required=False)
def shell(container_name):
    """Enter an interactive shell in a container."""
    shell_obj = ContainerShell()

    if not container_name:
        # Interactive mode
        shell_obj.interactive_mode()
    else:
        # Direct shell access
        if not container_name.startswith(shell_obj.container_prefix):
            container_name = f"{shell_obj.container_prefix}{container_name}"
        shell_obj.shell_into_container(container_name)


@cli.command()
@click.argument('container_name')
@click.argument('command')
def exec(container_name, command):
    """Execute a command in a container."""
    shell = ContainerShell()
    if not container_name.startswith(shell.container_prefix):
        container_name = f"{shell.container_prefix}{container_name}"

    exit_code, output = shell.execute_command(container_name, command)
    print(f"Exit code: {exit_code}")
    print(output)


@cli.command()
@click.argument('container_name')
def verify(container_name):
    """Run verification checks on a container."""
    shell = ContainerShell()
    if not container_name.startswith(shell.container_prefix):
        container_name = f"{shell.container_prefix}{container_name}"
    shell.verify_container(container_name)


@cli.command()
@click.argument('container_name')
def skills(container_name):
    """Inspect skills directory in a container."""
    shell = ContainerShell()
    if not container_name.startswith(shell.container_prefix):
        container_name = f"{shell.container_prefix}{container_name}"
    shell.inspect_skills(container_name)


@cli.command()
@click.argument('container_name')
def test(container_name):
    """Run test sequence to verify stateful shell."""
    shell = ContainerShell()
    if not container_name.startswith(shell.container_prefix):
        container_name = f"{shell.container_prefix}{container_name}"
    shell.run_test_sequence(container_name)


@cli.command()
@click.argument('container_name')
@click.option('--force', is_flag=True, help='Remove container after stopping')
def stop(container_name, force):
    """Stop and optionally remove a container."""
    shell = ContainerShell()
    if not container_name.startswith(shell.container_prefix):
        container_name = f"{shell.container_prefix}{container_name}"
    shell.cleanup_container(container_name, force)


@cli.command()
@click.option('--force', is_flag=True, help='Skip confirmation')
def cleanup(force):
    """Stop and remove all claude-agent containers."""
    shell = ContainerShell()
    containers = shell.list_containers(all_containers=True)

    if not containers:
        print(f"{Fore.YELLOW}No containers to clean up.{Style.RESET_ALL}")
        return

    if not force:
        print(f"{Fore.YELLOW}This will stop and remove {len(containers)} container(s):{Style.RESET_ALL}")
        for c in containers:
            print(f"  - {c['name']}")

        confirm = input(f"\n{Fore.RED}Are you sure? (y/N): {Style.RESET_ALL}").strip().lower()
        if confirm != 'y':
            print("Cancelled.")
            return

    for container in containers:
        shell.cleanup_container(container['name'], force=True)

    print(f"\n{Fore.GREEN}✓ Cleanup complete{Style.RESET_ALL}")


if __name__ == "__main__":
    # When run directly, enter interactive mode
    if len(sys.argv) == 1:
        shell = ContainerShell()
        shell.interactive_mode()
    else:
        cli()