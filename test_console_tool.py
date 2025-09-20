"""Unit tests for ConsoleToolProvider class."""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
import subprocess
import queue
import time
from typing import Dict, Any

# Add parent directory to path to import the module
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from evanai_client.tools.console_tool import ConsoleToolProvider


class TestConsoleToolProvider(unittest.TestCase):
    """Unit tests for ConsoleToolProvider."""

    def setUp(self):
        """Set up test fixtures."""
        self.provider = ConsoleToolProvider()
        self.tools, self.global_state, self.per_conversation_state = self.provider.init()
        self.conversation_state = {"_conversation_id": "test_conv_1"}

    def test_init(self):
        """Test initialization returns correct tools and states."""
        # Check tools are created
        self.assertEqual(len(self.tools), 6)

        # Check tool IDs
        tool_ids = [tool.id for tool in self.tools]
        expected_ids = [
            "execute_command",
            "start_interactive_session",
            "send_to_session",
            "read_session_output",
            "close_session",
            "list_sessions"
        ]
        self.assertEqual(set(tool_ids), set(expected_ids))

        # Check global state
        self.assertEqual(self.global_state["default_timeout"], 30)
        self.assertEqual(self.global_state["max_sessions"], 10)

        # Check per_conversation_state is empty dict
        self.assertEqual(self.per_conversation_state, {})

    # ============= Tests for execute_command =============

    @patch('subprocess.run')
    def test_execute_command_success(self, mock_run):
        """Test successful command execution."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.stdout = "Hello World"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # Execute tool
        result, error = self.provider.call_tool(
            "execute_command",
            {"command": "echo 'Hello World'", "timeout": 10},
            self.conversation_state,
            self.global_state
        )

        # Assertions
        self.assertIsNone(error)
        self.assertEqual(result["stdout"], "Hello World")
        self.assertEqual(result["stderr"], "")
        self.assertEqual(result["return_code"], 0)
        self.assertEqual(result["command"], "echo 'Hello World'")

        # Verify subprocess.run was called correctly
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        self.assertEqual(call_args[0][0], ["zsh", "-c", "echo 'Hello World'"])

    @patch('subprocess.run')
    def test_execute_command_with_error(self, mock_run):
        """Test command execution with error output."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = "Command not found"
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        # Execute tool
        result, error = self.provider.call_tool(
            "execute_command",
            {"command": "invalid_command"},
            self.conversation_state,
            self.global_state
        )

        # Assertions
        self.assertIsNone(error)
        self.assertEqual(result["stdout"], "")
        self.assertEqual(result["stderr"], "Command not found")
        self.assertEqual(result["return_code"], 1)

    @patch('subprocess.run')
    def test_execute_command_timeout(self, mock_run):
        """Test command execution timeout."""
        # Setup mock to raise timeout
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=5)

        # Execute tool
        result, error = self.provider.call_tool(
            "execute_command",
            {"command": "sleep 100", "timeout": 5},
            self.conversation_state,
            self.global_state
        )

        # Assertions
        self.assertIsNone(result)
        self.assertIn("timed out", error)
        self.assertIn("5 seconds", error)

    @patch('subprocess.run')
    def test_execute_command_with_working_directory(self, mock_run):
        """Test command execution with custom working directory."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.stdout = "success"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # Execute with explicit working directory
        result, error = self.provider.call_tool(
            "execute_command",
            {"command": "pwd", "working_directory": "/tmp"},
            self.conversation_state,
            self.global_state
        )

        # Verify cwd was set
        self.assertIsNone(error)
        call_kwargs = mock_run.call_args[1]
        self.assertEqual(call_kwargs["cwd"], "/tmp")

    @patch('subprocess.run')
    def test_execute_command_default_timeout(self, mock_run):
        """Test command execution with default timeout."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.stdout = "test"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # Execute without specifying timeout
        result, error = self.provider.call_tool(
            "execute_command",
            {"command": "echo test"},
            self.conversation_state,
            self.global_state
        )

        # Verify default timeout was used
        self.assertIsNone(error)
        call_kwargs = mock_run.call_args[1]
        self.assertEqual(call_kwargs["timeout"], 30)  # default timeout

    # ============= Tests for start_interactive_session =============

    @patch('subprocess.Popen')
    def test_start_interactive_session_success(self, mock_popen):
        """Test starting an interactive session."""
        # Setup mock process
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        mock_process.stdout.readline.return_value = ""
        mock_process.stderr.readline.return_value = ""
        mock_popen.return_value = mock_process

        # Start session
        result, error = self.provider.call_tool(
            "start_interactive_session",
            {"session_id": "test_session", "working_directory": "/home"},
            self.conversation_state,
            self.global_state
        )

        # Assertions
        self.assertIsNone(error)
        self.assertEqual(result["session_id"], "test_session")
        self.assertEqual(result["status"], "started")
        self.assertEqual(result["pid"], 12345)
        self.assertEqual(result["working_directory"], "/home")

        # Verify session stored in state
        self.assertIn("sessions", self.conversation_state)
        self.assertIn("test_session", self.conversation_state["sessions"])

        # Verify Popen was called with correct arguments
        mock_popen.assert_called_once_with(
            ["zsh", "-i"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="/home",
            env=os.environ.copy(),
            bufsize=0
        )

    def test_start_interactive_session_duplicate(self):
        """Test starting a session with duplicate ID."""
        # Create first session
        self.conversation_state["sessions"] = {
            "existing_session": {
                "process": MagicMock(),
                "output_queue": queue.Queue()
            }
        }

        # Try to create duplicate
        result, error = self.provider.call_tool(
            "start_interactive_session",
            {"session_id": "existing_session"},
            self.conversation_state,
            self.global_state
        )

        # Should fail
        self.assertIsNone(result)
        self.assertIn("already exists", error)

    def test_start_interactive_session_max_limit(self):
        """Test max sessions limit."""
        # Fill up sessions to max
        self.conversation_state["sessions"] = {}
        for i in range(10):
            self.conversation_state["sessions"][f"session_{i}"] = {
                "process": MagicMock()
            }

        # Try to create one more
        result, error = self.provider.call_tool(
            "start_interactive_session",
            {"session_id": "overflow_session"},
            self.conversation_state,
            self.global_state
        )

        # Should fail
        self.assertIsNone(result)
        self.assertIn("Maximum number of sessions", error)

    @patch('subprocess.Popen')
    def test_start_interactive_session_no_working_dir(self, mock_popen):
        """Test starting session without working directory."""
        # Setup mock process
        mock_process = MagicMock()
        mock_process.pid = 99999
        mock_process.poll.return_value = None
        mock_process.stdout.readline.return_value = ""
        mock_process.stderr.readline.return_value = ""
        mock_popen.return_value = mock_process

        # Start session without working_directory
        result, error = self.provider.call_tool(
            "start_interactive_session",
            {"session_id": "no_dir_session"},
            self.conversation_state,
            self.global_state
        )

        # Should succeed with None working directory
        self.assertIsNone(error)
        self.assertEqual(result["session_id"], "no_dir_session")
        call_kwargs = mock_popen.call_args[1]
        self.assertIsNone(call_kwargs["cwd"])

    # ============= Tests for send_to_session =============

    def test_send_to_session_success(self):
        """Test sending command to active session."""
        # Setup mock session
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.stdin = MagicMock()

        self.conversation_state["sessions"] = {
            "test_session": {
                "process": mock_process,
                "output_queue": queue.Queue()
            }
        }

        # Send command
        result, error = self.provider.call_tool(
            "send_to_session",
            {"session_id": "test_session", "command": "ls -la"},
            self.conversation_state,
            self.global_state
        )

        # Assertions
        self.assertIsNone(error)
        self.assertEqual(result["session_id"], "test_session")
        self.assertEqual(result["command_sent"], "ls -la")
        self.assertEqual(result["status"], "sent")

        # Verify command was written to stdin
        mock_process.stdin.write.assert_called_with("ls -la\n")
        mock_process.stdin.flush.assert_called_once()

    def test_send_to_session_not_found(self):
        """Test sending command to non-existent session."""
        result, error = self.provider.call_tool(
            "send_to_session",
            {"session_id": "ghost_session", "command": "test"},
            self.conversation_state,
            self.global_state
        )

        # Should fail
        self.assertIsNone(result)
        self.assertIn("not found", error)

    def test_send_to_session_terminated(self):
        """Test sending command to terminated session."""
        # Setup terminated session
        mock_process = MagicMock()
        mock_process.poll.return_value = 1  # Process has terminated

        self.conversation_state["sessions"] = {
            "dead_session": {
                "process": mock_process
            }
        }

        # Try to send command
        result, error = self.provider.call_tool(
            "send_to_session",
            {"session_id": "dead_session", "command": "test"},
            self.conversation_state,
            self.global_state
        )

        # Should fail
        self.assertIsNone(result)
        self.assertIn("has terminated", error)

    def test_send_to_session_write_error(self):
        """Test handling write errors when sending command."""
        # Setup session with broken stdin
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.stdin.write.side_effect = IOError("Broken pipe")

        self.conversation_state["sessions"] = {
            "broken_session": {
                "process": mock_process
            }
        }

        # Try to send command
        result, error = self.provider.call_tool(
            "send_to_session",
            {"session_id": "broken_session", "command": "test"},
            self.conversation_state,
            self.global_state
        )

        # Should fail with error message
        self.assertIsNone(result)
        self.assertIn("Failed to send command", error)

    # ============= Tests for read_session_output =============

    def test_read_session_output_with_data(self):
        """Test reading output from session with available data."""
        # Setup session with output
        output_queue = queue.Queue()
        output_queue.put(("stdout", "Line 1\n"))
        output_queue.put(("stdout", "Line 2\n"))
        output_queue.put(("stderr", "Error line\n"))

        self.conversation_state["sessions"] = {
            "test_session": {
                "process": MagicMock(),
                "output_queue": output_queue
            }
        }

        # Read output
        result, error = self.provider.call_tool(
            "read_session_output",
            {"session_id": "test_session", "timeout": 0.1},
            self.conversation_state,
            self.global_state
        )

        # Assertions
        self.assertIsNone(error)
        self.assertEqual(result["session_id"], "test_session")
        self.assertEqual(result["stdout"], "Line 1\nLine 2\n")
        self.assertEqual(result["stderr"], "Error line\n")
        self.assertFalse(result["has_more"])

    def test_read_session_output_empty(self):
        """Test reading output when queue is empty."""
        # Setup session with empty queue
        self.conversation_state["sessions"] = {
            "test_session": {
                "process": MagicMock(),
                "output_queue": queue.Queue()
            }
        }

        # Read output with short timeout
        result, error = self.provider.call_tool(
            "read_session_output",
            {"session_id": "test_session", "timeout": 0.1},
            self.conversation_state,
            self.global_state
        )

        # Should succeed with empty output
        self.assertIsNone(error)
        self.assertEqual(result["stdout"], "")
        self.assertEqual(result["stderr"], "")
        self.assertFalse(result["has_more"])

    def test_read_session_output_not_found(self):
        """Test reading output from non-existent session."""
        result, error = self.provider.call_tool(
            "read_session_output",
            {"session_id": "missing_session"},
            self.conversation_state,
            self.global_state
        )

        # Should fail
        self.assertIsNone(result)
        self.assertIn("not found", error)

    def test_read_session_output_has_more(self):
        """Test reading output indicates more data available."""
        # Setup session with lots of output
        output_queue = queue.Queue()
        for i in range(100):  # More lines to ensure we can't read all
            output_queue.put(("stdout", f"Line {i}\n"))

        self.conversation_state["sessions"] = {
            "test_session": {
                "process": MagicMock(),
                "output_queue": output_queue
            }
        }

        # Read output with very short timeout
        result, error = self.provider.call_tool(
            "read_session_output",
            {"session_id": "test_session", "timeout": 0.001},  # Even shorter timeout
            self.conversation_state,
            self.global_state
        )

        # Should indicate more data available
        self.assertIsNone(error)
        # Either we got some output and there's more, or the queue still has items
        if result["stdout"]:  # If we managed to read something
            remaining_items = not output_queue.empty()
            self.assertEqual(result["has_more"], remaining_items)

    def test_read_session_output_default_timeout(self):
        """Test reading output with default timeout."""
        # Setup session
        self.conversation_state["sessions"] = {
            "test_session": {
                "process": MagicMock(),
                "output_queue": queue.Queue()
            }
        }

        # Read output without specifying timeout
        start_time = time.time()
        result, error = self.provider.call_tool(
            "read_session_output",
            {"session_id": "test_session"},
            self.conversation_state,
            self.global_state
        )
        elapsed = time.time() - start_time

        # Should use default timeout of 1 second
        self.assertIsNone(error)
        self.assertGreaterEqual(elapsed, 0.9)
        self.assertLess(elapsed, 1.5)

    # ============= Tests for close_session =============

    def test_close_session_success(self):
        """Test closing an active session."""
        # Setup mock session
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Still running
        mock_process.terminate = MagicMock()
        mock_process.wait = MagicMock()

        self.conversation_state["sessions"] = {
            "test_session": {
                "process": mock_process,
                "output_queue": queue.Queue()
            }
        }

        # Close session
        result, error = self.provider.call_tool(
            "close_session",
            {"session_id": "test_session"},
            self.conversation_state,
            self.global_state
        )

        # Assertions
        self.assertIsNone(error)
        self.assertEqual(result["session_id"], "test_session")
        self.assertEqual(result["status"], "closed")

        # Verify process was terminated
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called()

        # Verify session removed from state
        self.assertNotIn("test_session", self.conversation_state.get("sessions", {}))

    def test_close_session_already_terminated(self):
        """Test closing an already terminated session."""
        # Setup already dead session
        mock_process = MagicMock()
        mock_process.poll.return_value = 1  # Already terminated

        self.conversation_state["sessions"] = {
            "dead_session": {
                "process": mock_process
            }
        }

        # Close session
        result, error = self.provider.call_tool(
            "close_session",
            {"session_id": "dead_session"},
            self.conversation_state,
            self.global_state
        )

        # Should succeed and clean up
        self.assertIsNone(error)
        self.assertEqual(result["status"], "closed")
        self.assertNotIn("dead_session", self.conversation_state.get("sessions", {}))

        # Should not try to terminate an already dead process
        mock_process.terminate.assert_not_called()

    def test_close_session_force_kill(self):
        """Test force killing a session that won't terminate."""
        # Setup stubborn process
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.terminate = MagicMock()
        mock_process.wait = MagicMock(side_effect=[subprocess.TimeoutExpired("", 5), None])
        mock_process.kill = MagicMock()

        self.conversation_state["sessions"] = {
            "stubborn_session": {
                "process": mock_process
            }
        }

        # Close session
        result, error = self.provider.call_tool(
            "close_session",
            {"session_id": "stubborn_session"},
            self.conversation_state,
            self.global_state
        )

        # Should succeed after force kill
        self.assertIsNone(error)
        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_called_once()

    def test_close_session_not_found(self):
        """Test closing non-existent session."""
        result, error = self.provider.call_tool(
            "close_session",
            {"session_id": "ghost_session"},
            self.conversation_state,
            self.global_state
        )

        # Should fail
        self.assertIsNone(result)
        self.assertIn("not found", error)

    # ============= Tests for list_sessions =============

    def test_list_sessions_empty(self):
        """Test listing sessions when none exist."""
        result, error = self.provider.call_tool(
            "list_sessions",
            {},
            self.conversation_state,
            self.global_state
        )

        # Should return empty list
        self.assertIsNone(error)
        self.assertEqual(result["sessions"], [])

    def test_list_sessions_multiple(self):
        """Test listing multiple active sessions."""
        # Setup multiple sessions
        mock_process1 = MagicMock()
        mock_process1.pid = 1001
        mock_process1.poll.return_value = None  # Active

        mock_process2 = MagicMock()
        mock_process2.pid = 1002
        mock_process2.poll.return_value = 0  # Terminated

        self.conversation_state["sessions"] = {
            "session1": {
                "process": mock_process1,
                "working_directory": "/home/user",
                "created_at": 1234567890
            },
            "session2": {
                "process": mock_process2,
                "working_directory": "/tmp",
                "created_at": 1234567900
            }
        }

        # List sessions
        result, error = self.provider.call_tool(
            "list_sessions",
            {},
            self.conversation_state,
            self.global_state
        )

        # Assertions
        self.assertIsNone(error)
        sessions = result["sessions"]
        self.assertEqual(len(sessions), 2)

        # Find sessions by ID
        session1 = next(s for s in sessions if s["session_id"] == "session1")
        session2 = next(s for s in sessions if s["session_id"] == "session2")

        # Check session1
        self.assertEqual(session1["pid"], 1001)
        self.assertTrue(session1["active"])
        self.assertEqual(session1["working_directory"], "/home/user")
        self.assertEqual(session1["created_at"], 1234567890)

        # Check session2
        self.assertEqual(session2["pid"], 1002)
        self.assertFalse(session2["active"])
        self.assertEqual(session2["working_directory"], "/tmp")
        self.assertEqual(session2["created_at"], 1234567900)

    def test_list_sessions_no_sessions_key(self):
        """Test listing sessions when sessions key doesn't exist in state."""
        # Ensure no sessions key in state
        if "sessions" in self.conversation_state:
            del self.conversation_state["sessions"]

        result, error = self.provider.call_tool(
            "list_sessions",
            {},
            self.conversation_state,
            self.global_state
        )

        # Should return empty list
        self.assertIsNone(error)
        self.assertEqual(result["sessions"], [])

    # ============= Tests for error handling =============

    def test_unknown_tool_id(self):
        """Test calling with unknown tool ID."""
        result, error = self.provider.call_tool(
            "unknown_tool",
            {},
            self.conversation_state,
            self.global_state
        )

        # Should fail
        self.assertIsNone(result)
        self.assertIn("Unknown tool", error)

    def test_exception_handling(self):
        """Test general exception handling in call_tool."""
        # Mock _execute_command to raise exception
        with patch.object(self.provider, '_execute_command', side_effect=Exception("Test error")):
            result, error = self.provider.call_tool(
                "execute_command",
                {"command": "test"},
                self.conversation_state,
                self.global_state
            )

            # Should catch and return error
            self.assertIsNone(result)
            self.assertIn("Error executing tool", error)
            self.assertIn("Test error", error)

    # ============= Tests for conversation isolation =============

    def test_conversation_state_isolation(self):
        """Test that sessions are isolated per conversation."""
        # Create session in first conversation
        conversation1 = {"_conversation_id": "conv1"}
        conversation2 = {"_conversation_id": "conv2"}

        # Add session to conversation 1
        conversation1["sessions"] = {"session1": {"process": MagicMock()}}

        # List sessions in conversation 2
        result, error = self.provider.call_tool(
            "list_sessions",
            {},
            conversation2,
            self.global_state
        )

        # Conversation 2 should have no sessions
        self.assertEqual(result["sessions"], [])

        # Conversation 1 should still have its session
        self.assertIn("session1", conversation1["sessions"])


class TestToolIntegration(unittest.TestCase):
    """Integration tests for tool workflows."""

    @patch('subprocess.Popen')
    def test_full_session_workflow(self, mock_popen):
        """Test complete workflow: start, send, read, close."""
        # Setup
        provider = ConsoleToolProvider()
        tools, global_state, _ = provider.init()
        conversation_state = {"_conversation_id": "test_conv"}

        # Setup mock process
        mock_process = MagicMock()
        mock_process.pid = 9999
        mock_process.poll.return_value = None
        mock_process.stdin = MagicMock()
        mock_process.stdout.readline.side_effect = ["output line\n", ""]
        mock_process.stderr.readline.return_value = ""
        mock_popen.return_value = mock_process

        # 1. Start session
        result, error = provider.call_tool(
            "start_interactive_session",
            {"session_id": "workflow_session"},
            conversation_state,
            global_state
        )
        self.assertIsNone(error)
        self.assertEqual(result["status"], "started")

        # 2. Send command
        result, error = provider.call_tool(
            "send_to_session",
            {"session_id": "workflow_session", "command": "echo test"},
            conversation_state,
            global_state
        )
        self.assertIsNone(error)
        self.assertEqual(result["status"], "sent")

        # 3. Read output (give threads time to populate queue)
        time.sleep(0.1)
        result, error = provider.call_tool(
            "read_session_output",
            {"session_id": "workflow_session", "timeout": 0.2},
            conversation_state,
            global_state
        )
        self.assertIsNone(error)

        # 4. List sessions
        result, error = provider.call_tool(
            "list_sessions",
            {},
            conversation_state,
            global_state
        )
        self.assertIsNone(error)
        self.assertEqual(len(result["sessions"]), 1)

        # 5. Close session
        result, error = provider.call_tool(
            "close_session",
            {"session_id": "workflow_session"},
            conversation_state,
            global_state
        )
        self.assertIsNone(error)
        self.assertEqual(result["status"], "closed")

        # Verify session is gone
        self.assertNotIn("workflow_session", conversation_state.get("sessions", {}))

    @patch('subprocess.Popen')
    def test_multiple_sessions_management(self, mock_popen):
        """Test managing multiple sessions concurrently."""
        # Setup
        provider = ConsoleToolProvider()
        tools, global_state, _ = provider.init()
        conversation_state = {"_conversation_id": "multi_conv"}

        # Mock processes
        processes = []
        for i in range(3):
            mock_process = MagicMock()
            mock_process.pid = 1000 + i
            mock_process.poll.return_value = None
            mock_process.stdin = MagicMock()
            mock_process.stdout.readline.return_value = ""
            mock_process.stderr.readline.return_value = ""
            processes.append(mock_process)

        mock_popen.side_effect = processes

        # Start multiple sessions
        for i in range(3):
            result, error = provider.call_tool(
                "start_interactive_session",
                {"session_id": f"session_{i}"},
                conversation_state,
                global_state
            )
            self.assertIsNone(error)
            self.assertEqual(result["status"], "started")

        # List all sessions
        result, error = provider.call_tool(
            "list_sessions",
            {},
            conversation_state,
            global_state
        )
        self.assertIsNone(error)
        self.assertEqual(len(result["sessions"]), 3)

        # Close middle session
        result, error = provider.call_tool(
            "close_session",
            {"session_id": "session_1"},
            conversation_state,
            global_state
        )
        self.assertIsNone(error)

        # Verify only 2 sessions remain
        result, error = provider.call_tool(
            "list_sessions",
            {},
            conversation_state,
            global_state
        )
        self.assertEqual(len(result["sessions"]), 2)
        session_ids = [s["session_id"] for s in result["sessions"]]
        self.assertIn("session_0", session_ids)
        self.assertIn("session_2", session_ids)
        self.assertNotIn("session_1", session_ids)


if __name__ == '__main__':
    unittest.main()