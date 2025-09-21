"""
Configuration for the Bash tool.

This module provides configuration and setup utilities for the Bash tool.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional


class BashToolConfig:
    """Configuration manager for the Bash tool."""

    DEFAULT_CONFIG = {
        "runtime_dir": "./evanai_runtime",
        "docker_image": "claude-agent:latest",
        "idle_timeout": 0,  # 0 = no timeout
        "memory_limit": "2g",
        "cpu_limit": 2.0,
        "max_agents": 100,
        "auto_cleanup": True,
        "enable_logging": True,
        "network_name": "agent-network"
    }

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            config_file: Path to configuration file (JSON)
        """
        self.config_file = config_file or os.environ.get(
            'BASH_TOOL_CONFIG',
            './bash_tool_config.json'
        )
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        config = self.DEFAULT_CONFIG.copy()

        # Override with environment variables
        env_mappings = {
            'EVANAI_RUNTIME_DIR': 'runtime_dir',
            'BASH_TOOL_IMAGE': 'docker_image',
            'BASH_TOOL_IDLE_TIMEOUT': 'idle_timeout',
            'BASH_TOOL_MEMORY_LIMIT': 'memory_limit',
            'BASH_TOOL_CPU_LIMIT': 'cpu_limit',
            'BASH_TOOL_MAX_AGENTS': 'max_agents'
        }

        for env_var, config_key in env_mappings.items():
            if env_var in os.environ:
                value = os.environ[env_var]

                # Convert numeric values
                if config_key in ['idle_timeout', 'max_agents']:
                    value = int(value)
                elif config_key == 'cpu_limit':
                    value = float(value)
                elif config_key == 'auto_cleanup':
                    value = value.lower() in ['true', '1', 'yes']

                config[config_key] = value

        # Override with config file if exists
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    config.update(file_config)
                    print(f"[BashToolConfig] Loaded config from {self.config_file}")
            except Exception as e:
                print(f"[BashToolConfig] Error loading config file: {e}")

        return config

    def save_config(self, config_file: Optional[str] = None):
        """Save current configuration to file."""
        file_path = config_file or self.config_file

        with open(file_path, 'w') as f:
            json.dump(self.config, f, indent=2)

        print(f"[BashToolConfig] Saved config to {file_path}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """Set configuration value."""
        self.config[key] = value

    def validate(self) -> bool:
        """Validate configuration settings."""
        errors = []

        # Check runtime directory
        runtime_dir = Path(self.config['runtime_dir'])
        if not runtime_dir.exists():
            try:
                runtime_dir.mkdir(parents=True, exist_ok=True)
                print(f"[BashToolConfig] Created runtime directory: {runtime_dir}")
            except Exception as e:
                errors.append(f"Cannot create runtime directory: {e}")

        # Check Docker availability
        try:
            import docker
            client = docker.from_env()
            client.ping()
        except Exception as e:
            errors.append(f"Docker not available: {e}")

        # Check if image exists
        try:
            client.images.get(self.config['docker_image'])
        except:
            errors.append(f"Docker image not found: {self.config['docker_image']}")

        # Validate limits
        if self.config['cpu_limit'] <= 0:
            errors.append("CPU limit must be positive")

        if self.config['max_agents'] <= 0:
            errors.append("Max agents must be positive")

        # Parse memory limit
        import re
        mem_pattern = re.compile(r'^(\d+)([kmg]?)b?$', re.IGNORECASE)
        match = mem_pattern.match(str(self.config['memory_limit']))
        if not match:
            errors.append(f"Invalid memory limit format: {self.config['memory_limit']}")

        if errors:
            print("[BashToolConfig] Validation errors:")
            for error in errors:
                print(f"  - {error}")
            return False

        print("[BashToolConfig] Configuration valid")
        return True

    def create_bash_tool_provider(self):
        """Create a BashToolProvider with current configuration."""
        from .bash_tool import BashToolProvider

        return BashToolProvider(
            runtime_dir=self.config['runtime_dir'],
            idle_timeout=self.config['idle_timeout'],
            memory_limit=self.config['memory_limit'],
            cpu_limit=self.config['cpu_limit'],
            image=self.config['docker_image'],
            auto_cleanup=self.config['auto_cleanup'],
            enable_logging=self.config['enable_logging']
        )

    def __repr__(self):
        """String representation."""
        return f"BashToolConfig({self.config})"


def setup_bash_tool(
    runtime_dir: Optional[str] = None,
    check_docker: bool = True,
    build_image: bool = False
) -> bool:
    """
    Setup the Bash tool environment.

    Args:
        runtime_dir: Runtime directory for agent data
        check_docker: Check Docker availability
        build_image: Build the Docker image if not found

    Returns:
        True if setup successful
    """
    print("Setting up Bash Tool Environment")
    print("=" * 40)

    # Create config
    config = BashToolConfig()

    if runtime_dir:
        config.set('runtime_dir', runtime_dir)

    # Create directories
    runtime_path = Path(config.get('runtime_dir'))
    work_dir = runtime_path / "agent-working-directory"

    runtime_path.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    print(f"✓ Runtime directory: {runtime_path}")
    print(f"✓ Working directory: {work_dir}")

    # Check Docker
    if check_docker:
        try:
            import docker
            client = docker.from_env()
            client.ping()
            print("✓ Docker is available")

            # Check for image
            image_name = config.get('docker_image')
            try:
                client.images.get(image_name)
                print(f"✓ Docker image found: {image_name}")
            except docker.errors.ImageNotFound:
                print(f"✗ Docker image not found: {image_name}")

                if build_image:
                    print("Building image...")
                    # Would run build script here
                    print("Please run: ./build-agent.sh")
                    return False

        except Exception as e:
            print(f"✗ Docker error: {e}")
            return False

    # Save default config
    config_file = Path("bash_tool_config.json")
    if not config_file.exists():
        config.save_config(str(config_file))
        print(f"✓ Created config file: {config_file}")

    print("\n✓ Bash tool environment ready!")
    return True


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Configure and setup Bash tool for EvanAI"
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Setup the Bash tool environment"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate current configuration"
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show current configuration"
    )
    parser.add_argument(
        "--runtime-dir",
        help="Set runtime directory"
    )
    parser.add_argument(
        "--save",
        help="Save configuration to file"
    )

    args = parser.parse_args()

    config = BashToolConfig()

    if args.runtime_dir:
        config.set('runtime_dir', args.runtime_dir)

    if args.setup:
        success = setup_bash_tool(
            runtime_dir=args.runtime_dir,
            check_docker=True
        )
        if not success:
            sys.exit(1)

    if args.validate:
        if not config.validate():
            sys.exit(1)

    if args.show:
        print("Current Configuration:")
        for key, value in config.config.items():
            print(f"  {key}: {value}")

    if args.save:
        config.save_config(args.save)
        print(f"Configuration saved to {args.save}")