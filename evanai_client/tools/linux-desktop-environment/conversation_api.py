#!/usr/bin/env python3
"""
Conversation-based API for lazy agent container management.

This demonstrates how Claude conversations would interact with
the lazy container system. Containers are only created when
the bash tool is actually invoked.
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from lazy_agent_manager import LazyAgentManager, ConversationAgent


# Request/Response models
class BashRequest(BaseModel):
    """Request to execute bash command in a conversation."""
    command: str = Field(..., description="Bash command to execute")
    timeout: Optional[int] = Field(None, description="Command timeout in seconds")


class BashResponse(BaseModel):
    """Response from bash command execution."""
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    conversation_id: str
    container_created: bool = Field(False, description="Was container created for this command")
    command_count: int = Field(0, description="Total commands executed in this conversation")
    execution_time_ms: int = Field(0, description="Command execution time in milliseconds")


class ConversationInfo(BaseModel):
    """Information about a conversation's agent."""
    conversation_id: str
    state: str
    container_active: bool
    command_count: int
    last_activity: Optional[str]
    uptime_seconds: Optional[float]
    idle_seconds: Optional[float]


class ConversationManager:
    """
    Manages conversation-to-agent mappings with lazy initialization.
    This simulates how Claude would manage different conversation contexts.
    """

    def __init__(self, runtime_dir: str = "./evanai_runtime"):
        self.manager = LazyAgentManager(
            runtime_dir=runtime_dir,
            default_idle_timeout=0,  # 0 = no timeout
            max_agents=50
        )
        self.conversations: Dict[str, Dict[str, Any]] = {}

    async def execute_bash(
        self,
        conversation_id: str,
        command: str,
        timeout: Optional[int] = None
    ) -> BashResponse:
        """
        Execute bash command for a conversation.
        Container is created lazily on first use.
        Uses host network for full network access.
        """
        # Track if this is first command
        is_first_command = conversation_id not in self.conversations

        if is_first_command:
            self.conversations[conversation_id] = {
                "created_at": datetime.now(),
                "command_count": 0
            }
            print(f"[API] New conversation: {conversation_id}")

        # Record container state before execution
        stats_before = self.manager.get_stats()
        container_existed = any(
            a["agent_id"] == conversation_id and a["state"] != "not_created"
            for a in stats_before["agents"]
        )

        # Execute command (may create container)
        start_time = datetime.now()
        result = self.manager.execute_bash(conversation_id, command, timeout)
        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        # Update conversation tracking
        self.conversations[conversation_id]["command_count"] += 1
        self.conversations[conversation_id]["last_command"] = datetime.now()

        # Check if container was created
        container_created = is_first_command or not container_existed

        if container_created:
            print(f"[API] Container created for conversation: {conversation_id}")

        return BashResponse(
            success=result["success"],
            exit_code=result["exit_code"],
            stdout=result["stdout"],
            stderr=result["stderr"],
            conversation_id=conversation_id,
            container_created=container_created,
            command_count=result["command_count"],
            execution_time_ms=int(execution_time)
        )

    async def get_conversation_info(self, conversation_id: str) -> Optional[ConversationInfo]:
        """Get information about a conversation's agent."""
        stats = self.manager.get_stats()

        for agent_stats in stats["agents"]:
            if agent_stats["agent_id"] == conversation_id:
                return ConversationInfo(
                    conversation_id=conversation_id,
                    state=agent_stats["state"],
                    container_active=agent_stats["state"] == "running",
                    command_count=agent_stats["command_count"],
                    last_activity=agent_stats.get("last_activity"),
                    uptime_seconds=agent_stats.get("uptime_seconds"),
                    idle_seconds=agent_stats.get("idle_seconds")
                )

        # Conversation exists but no container yet
        if conversation_id in self.conversations:
            return ConversationInfo(
                conversation_id=conversation_id,
                state="not_created",
                container_active=False,
                command_count=0,
                last_activity=None,
                uptime_seconds=None,
                idle_seconds=None
            )

        return None

    async def cleanup_conversation(self, conversation_id: str, remove_data: bool = True):
        """Clean up a conversation's container."""
        self.manager.cleanup_conversation(conversation_id, remove_data)
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]

    async def get_all_conversations(self) -> List[ConversationInfo]:
        """Get info about all conversations."""
        conversations = []

        stats = self.manager.get_stats()
        for agent_stats in stats["agents"]:
            conversations.append(
                ConversationInfo(
                    conversation_id=agent_stats["agent_id"],
                    state=agent_stats["state"],
                    container_active=agent_stats["state"] == "running",
                    command_count=agent_stats["command_count"],
                    last_activity=agent_stats.get("last_activity"),
                    uptime_seconds=agent_stats.get("uptime_seconds"),
                    idle_seconds=agent_stats.get("idle_seconds")
                )
            )

        return conversations


# Global conversation manager
conversation_mgr = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global conversation_mgr

    # Startup
    print("Starting Conversation API...")
    conversation_mgr = ConversationManager()
    print("API ready")

    yield

    # Shutdown
    print("Shutting down...")
    if conversation_mgr:
        conversation_mgr.manager.cleanup_all()
    print("Cleanup complete")


# Create FastAPI app
app = FastAPI(
    title="Claude Agent Conversation API",
    description="Lazy container management for conversation-based agents",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """API information."""
    return {
        "service": "Claude Agent Conversation API",
        "status": "ready",
        "endpoints": {
            "execute_bash": "POST /conversations/{conversation_id}/bash",
            "conversation_info": "GET /conversations/{conversation_id}",
            "list_conversations": "GET /conversations",
            "cleanup": "DELETE /conversations/{conversation_id}",
            "stats": "GET /stats"
        }
    }


@app.post("/conversations/{conversation_id}/bash", response_model=BashResponse)
async def execute_bash(
    conversation_id: str,
    request: BashRequest,
    background_tasks: BackgroundTasks
):
    """
    Execute bash command in a conversation's container.

    Container is created lazily on first command.
    Subsequent commands reuse the same container.
    Container auto-stops after idle timeout.
    """
    try:
        result = await conversation_mgr.execute_bash(
            conversation_id,
            request.command,
            request.timeout
        )

        # Log for demonstration
        if result.container_created:
            background_tasks.add_task(
                print,
                f"[Background] Container created for {conversation_id}"
            )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversations/{conversation_id}", response_model=ConversationInfo)
async def get_conversation(conversation_id: str):
    """Get information about a conversation's agent."""
    info = await conversation_mgr.get_conversation_info(conversation_id)

    if not info:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return info


@app.get("/conversations", response_model=List[ConversationInfo])
async def list_conversations():
    """List all active conversations."""
    return await conversation_mgr.get_all_conversations()


@app.delete("/conversations/{conversation_id}")
async def cleanup_conversation(
    conversation_id: str,
    remove_data: bool = True
):
    """Clean up a conversation's container and optionally its data."""
    info = await conversation_mgr.get_conversation_info(conversation_id)

    if not info:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await conversation_mgr.cleanup_conversation(conversation_id, remove_data)

    return {
        "status": "cleaned",
        "conversation_id": conversation_id,
        "data_removed": remove_data
    }


@app.get("/stats")
async def get_stats():
    """Get system statistics."""
    stats = conversation_mgr.manager.get_stats()

    return {
        "total_conversations": len(conversation_mgr.conversations),
        "total_agents": stats["total_agents"],
        "agents_by_state": stats["agents_by_state"],
        "total_commands": stats["total_commands"],
        "conversations": [
            {
                "id": cid,
                "command_count": data["command_count"],
                "created_at": data["created_at"].isoformat()
            }
            for cid, data in conversation_mgr.conversations.items()
        ]
    }


@app.post("/demo/simulate-claude-conversation")
async def simulate_claude_conversation():
    """
    Simulate a Claude conversation with bash tool usage.
    Shows lazy container initialization.
    """
    import uuid
    conversation_id = f"claude-{uuid.uuid4().hex[:8]}"

    results = []

    # Simulate conversation flow
    steps = [
        {
            "message": "User asks Claude to check system info",
            "bash_command": "uname -a && python3 --version"
        },
        {
            "message": "Claude writes a Python script",
            "bash_command": "cat > /mnt/hello.py << 'EOF'\nprint('Hello from Claude!')\nEOF"
        },
        {
            "message": "Claude runs the script",
            "bash_command": "cd /mnt && python3 hello.py"
        },
        {
            "message": "Claude checks the results",
            "bash_command": "ls -la /mnt/"
        }
    ]

    for i, step in enumerate(steps, 1):
        # Execute bash command
        result = await conversation_mgr.execute_bash(
            conversation_id,
            step["bash_command"]
        )

        results.append({
            "step": i,
            "message": step["message"],
            "command": step["bash_command"],
            "container_created": result.container_created,
            "output": result.stdout[:200] if result.success else result.stderr[:200],
            "success": result.success
        })

        # Note when container is created
        if result.container_created:
            results[-1]["note"] = "Container lazily created on first bash usage"

        await asyncio.sleep(0.5)  # Simulate thinking time

    # Get final stats
    info = await conversation_mgr.get_conversation_info(conversation_id)

    return {
        "conversation_id": conversation_id,
        "simulation": results,
        "final_stats": {
            "total_commands": info.command_count,
            "container_state": info.state,
            "uptime_seconds": info.uptime_seconds
        },
        "explanation": (
            "Container was created only when first bash command was executed, "
            "not when conversation started. All subsequent commands reused "
            "the same container."
        )
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        stats = conversation_mgr.manager.get_stats()
        return {
            "status": "healthy",
            "agents": stats["total_agents"],
            "conversations": len(conversation_mgr.conversations)
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


if __name__ == "__main__":
    # Run the API server
    print("Starting Conversation API Server...")
    print("API will be available at http://localhost:8000")
    print("Documentation at http://localhost:8000/docs")
    print()
    print("Example usage:")
    print("  curl -X POST http://localhost:8000/conversations/test-001/bash \\")
    print("    -H 'Content-Type: application/json' \\")
    print("    -d '{\"command\": \"echo Hello World\"}'")
    print()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )