"""Upload tools for submitting files to the user."""

import requests
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from ..tool_system import BaseToolSetProvider, Tool, Parameter, ParameterType
from ..constants import FILE_UPLOAD_API_URL, BROADCAST_API_URL


class UploadToolProvider(BaseToolSetProvider):
    """Provides tools for uploading files to the user."""

    def __init__(self, websocket_handler=None):
        super().__init__(websocket_handler)
        self.upload_url = FILE_UPLOAD_API_URL

    def init(self) -> Tuple[List[Tool], Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """Initialize upload tools."""
        tools = [
            Tool(
                id="submit_file_to_user",
                name="Submit File to User",
                display_name="Submit File to User",
                description="Submit a file to the user for download. IMPORTANT: Files MUST be in the conversation_data folder - this tool ONLY works with files inside conversation_data/. Files elsewhere in the workspace cannot be uploaded. Save any files you want to submit into conversation_data/ first.",
                parameters={
                    "path": Parameter(
                        name="path",
                        type=ParameterType.STRING,
                        description="Path to the file (MUST start with 'conversation_data/'). Example: 'conversation_data/report.pdf'. Files outside conversation_data cannot be uploaded - save them there first.",
                        required=True
                    ),
                    "description": Parameter(
                        name="description",
                        type=ParameterType.STRING,
                        description="Natural language description of what this file is for and what it contains",
                        required=True
                    )
                }
            )
        ]

        # Track upload statistics
        global_state = {
            "total_uploads": 0,
            "total_bytes_uploaded": 0
        }

        # Per-conversation state for tracking uploads
        per_conversation_state = {}

        return tools, global_state, per_conversation_state

    def call_tool(
        self,
        tool_id: str,
        tool_parameters: Dict[str, Any],
        per_conversation_state: Dict[str, Any],
        global_state: Dict[str, Any]
    ) -> Tuple[Any, Optional[str]]:
        """Execute an upload tool."""

        # Get the working directory from conversation state
        working_directory = per_conversation_state.get('_working_directory')
        if not working_directory:
            return None, "Error: Working directory not available for this conversation"

        if tool_id == "submit_file_to_user":
            return self._submit_file_to_user(
                tool_parameters,
                working_directory,
                per_conversation_state,
                global_state
            )
        else:
            return None, f"Unknown tool: {tool_id}"

    def _submit_file_to_user(
        self,
        params: Dict[str, Any],
        working_directory: str,
        per_conversation_state: Dict[str, Any],
        global_state: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """Submit a file to the user via upload API."""
        file_path = params.get("path")
        description = params.get("description")

        if not file_path:
            return None, "Error: Path parameter is required"

        if not description:
            return None, "Error: Description parameter is required"

        # Strip /mnt/ prefix if present (agent might use absolute paths)
        if file_path.startswith("/mnt/"):
            file_path = file_path[5:]  # Remove "/mnt/" (5 characters)

        # Parse working directory to find conversation_data symlink
        working_path = Path(working_directory)
        conversation_data_link = working_path / "conversation_data"

        if not conversation_data_link.exists():
            return None, "Error: conversation_data folder not found in working directory"

        # The file must be in conversation_data folder
        try:
            # Build the full path
            file_path_obj = Path(file_path)

            # Check if the path starts with conversation_data
            if not file_path.startswith("conversation_data/"):
                return None, "Error: File must be in conversation_data folder. Path should start with 'conversation_data/'"

            # Get the relative path within conversation_data
            relative_path = Path(file_path).relative_to("conversation_data")

            # Resolve the actual file path
            full_file_path = (conversation_data_link / relative_path).resolve()

            # Verify the file exists
            if not full_file_path.exists():
                return None, f"Error: File does not exist: {file_path}"

            if not full_file_path.is_file():
                return None, f"Error: Path is not a file: {file_path}"

            # Verify the file is actually within conversation_data (security check)
            conv_data_resolved = conversation_data_link.resolve()
            if not str(full_file_path).startswith(str(conv_data_resolved)):
                return None, "Error: File must be inside conversation_data folder"

            # Read the file for upload
            file_size = full_file_path.stat().st_size

            # Upload the file
            try:
                with open(full_file_path, 'rb') as f:
                    files = {'file': (full_file_path.name, f, 'application/octet-stream')}

                    # Disable SSL verification as in websocket_handler.py
                    import warnings
                    from urllib3.exceptions import InsecureRequestWarning
                    warnings.filterwarnings('ignore', category=InsecureRequestWarning)

                    response = requests.post(
                        self.upload_url,
                        files=files,
                        verify=False  # Disable SSL verification for testing
                    )
                    response.raise_for_status()

                upload_result = response.json()

                if not upload_result.get("success"):
                    return None, f"Error: Upload failed - {upload_result.get('error', 'Unknown error')}"

                # Update statistics
                global_state["total_uploads"] = global_state.get("total_uploads", 0) + 1
                global_state["total_bytes_uploaded"] = global_state.get("total_bytes_uploaded", 0) + file_size

                # Track in conversation state
                per_conversation_state.setdefault("uploaded_files", []).append({
                    "path": file_path,
                    "description": description,
                    "filename": upload_result.get("fileName"),
                    "size": file_size
                })

                # Broadcast the upload to the user device
                conversation_id = per_conversation_state.get('_conversation_id')
                if self.websocket_handler and conversation_id:
                    # Get the download URL from the upload result
                    download_url = upload_result.get("downloadUrl")

                    # Prepare the broadcast message
                    broadcast_message = {
                        "recipient": "user_device",
                        "type": "agent_file_upload",
                        "payload": {
                            "conversation_id": conversation_id,
                            "resource_url": download_url,
                            "description": description
                        }
                    }

                    # Send the broadcast
                    try:
                        broadcast_url = BROADCAST_API_URL
                        broadcast_data = {
                            "device": "evanai-client",
                            "format": "file_upload",
                            "recipient": "user_device",
                            "type": "agent_file_upload",
                            "payload": {
                                "conversation_id": conversation_id,
                                "resource_url": download_url,
                                "description": description
                            },
                            "timestamp": int(datetime.now().timestamp() * 1000)
                        }

                        # Disable SSL verification as in other places
                        import warnings
                        from urllib3.exceptions import InsecureRequestWarning
                        warnings.filterwarnings('ignore', category=InsecureRequestWarning)

                        broadcast_response = requests.post(
                            broadcast_url,
                            json=broadcast_data,
                            verify=False
                        )
                        broadcast_response.raise_for_status()
                        print(f"Broadcast file upload notification to user device")
                    except Exception as e:
                        print(f"Warning: Failed to broadcast file upload notification: {e}")
                        # Don't fail the upload if broadcast fails

                # Return success without revealing the URL to the agent
                return {
                    "success": True,
                    "message": f"File successfully uploaded to user",
                    "file_path": file_path,
                    "description": description,
                    "file_size": file_size,
                    "upload_filename": upload_result.get("fileName")
                }, None

            except requests.exceptions.RequestException as e:
                return None, f"Error: Failed to upload file - {str(e)}"
            except Exception as e:
                return None, f"Error: Failed to read or upload file - {str(e)}"

        except ValueError as e:
            return None, f"Error: Invalid path - {str(e)}"
        except Exception as e:
            return None, f"Error: Failed to process file path - {str(e)}"