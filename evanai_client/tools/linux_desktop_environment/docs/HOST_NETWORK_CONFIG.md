# Host Network Configuration for Agent Containers

## Overview

The agent containers have been configured to use **host network mode** instead of isolated Docker networks. This gives agents full access to the host's network stack, allowing them to:

- Access host services (localhost/127.0.0.1)
- Connect to external services without NAT
- Bind to host ports directly
- Use the host's DNS resolution
- Access local network resources

## Changes Made

### 1. Container Configuration
All Docker containers now use `network_mode: host` instead of isolated bridge networks:

```yaml
# Before (isolated network)
network: agent-network

# After (host network)
network_mode: host
```

### 2. Network Capabilities
Added network capabilities to containers:
- `NET_RAW` - For raw socket access
- `NET_BIND_SERVICE` - To bind to privileged ports

### 3. Files Updated

- **lazy_agent_manager.py**
  - Removed network creation
  - Set `network_mode: "host"` in container config

- **agent_manager.py**
  - Removed network setup
  - Updated container creation with host network

- **launch-agent.sh**
  - Removed network creation commands
  - Added `--network host` to Docker run

- **docker-compose.agent.yml**
  - Replaced network configuration with `network_mode: host`
  - Removed networks section

- **bash_tool.py**
  - Updated tool description to mention network access
  - Added configuration for host network

## Security Implications

Using host network mode means:

⚠️ **Less Isolation**: Containers can access all host network services
⚠️ **Port Conflicts**: Containers share the host's port space
⚠️ **Network Visibility**: Containers see all network interfaces

✅ **Still Secure**:
- Read-only root filesystem maintained
- Only `/mnt` is writable
- Resource limits still enforced
- Capabilities still restricted (except network)

## Usage Examples

### Accessing Host Services

```python
# Agent can now access host services
result = tool_manager.call_tool(
    "bash",
    {"command": "curl http://localhost:8080"},  # Works with host services
    conversation_id
)
```

### Network Operations

```python
# Full network access
result = tool_manager.call_tool(
    "bash",
    {"command": "ping google.com"},  # External connectivity
    conversation_id
)

# Access host database
result = tool_manager.call_tool(
    "bash",
    {"command": "psql -h localhost -U user -d database -c 'SELECT 1'"},
    conversation_id
)
```

### Binding to Ports

```python
# Agent can bind to host ports
result = tool_manager.call_tool(
    "bash",
    {"command": "python3 -m http.server 8888"},  # Accessible on host:8888
    conversation_id
)
```

## Configuration

### Environment Variables

No changes needed - host network is now the default.

### Reverting to Isolated Network

If you need to revert to isolated networks:

1. Edit `lazy_agent_manager.py`:
```python
# Change from:
"network_mode": "host"
# To:
"network": "agent-network"
```

2. Recreate the network setup code
3. Remove network capabilities from cap_add

## Testing Host Network

```bash
# Test 1: Access localhost
docker run --rm --network host claude-agent:latest \
  bash -c "curl -s http://localhost:80 | head -5"

# Test 2: Check network interfaces (should see host's)
docker run --rm --network host claude-agent:latest \
  bash -c "ip addr show"

# Test 3: Verify DNS resolution uses host's
docker run --rm --network host claude-agent:latest \
  bash -c "cat /etc/resolv.conf"
```

## Performance Benefits

Host network mode provides:
- **No NAT overhead**: Direct network access
- **Better performance**: No bridge network latency
- **Simpler debugging**: Network traffic visible on host

## Monitoring

```bash
# See all connections from agents
netstat -tuln | grep ESTABLISHED

# Monitor agent network usage
iftop  # Shows real-time network usage

# Check which ports agents are using
lsof -i -P | grep claude-agent
```

## Best Practices

1. **Port Management**: Track which ports agents use to avoid conflicts
2. **Service Access**: Be aware agents can access ALL host services
3. **Firewall Rules**: Host firewall rules apply to agent traffic
4. **Resource Limits**: Still important even with host network

## Troubleshooting

### Port Already in Use
```bash
# Find what's using a port
lsof -i :8080

# Agent trying to bind to used port will fail
Error: bind: address already in use
```

### Cannot Access External Network
- Check host firewall rules
- Verify host has internet connectivity
- Check proxy settings if behind corporate firewall

### Service Discovery
```bash
# Agents can discover host services
docker exec claude-agent-xxx bash -c "ss -tuln"
```

## Summary

The agent containers now use host network mode, providing:
- Full access to host network services
- Better performance (no NAT/bridge overhead)
- Simplified service integration
- Direct external connectivity

While this reduces network isolation, other security measures remain in place (read-only filesystem, resource limits, capability restrictions).