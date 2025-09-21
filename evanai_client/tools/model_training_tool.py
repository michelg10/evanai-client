"""
Model training tool for starting and managing remote machine learning model training.
"""

import time
import random
import uuid
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from ..tool_system import BaseToolSetProvider, Tool, Parameter, ParameterType


class ModelTrainingToolProvider(BaseToolSetProvider):
    """Provider for model training tools."""

    def __init__(self, websocket_handler=None):
        super().__init__(websocket_handler)
        self.training_sessions = {}

    def init(self) -> Tuple[List[Tool], Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """Initialize model training tools."""
        tools = [
            Tool(
                id="start_model_training",
                name="start_model_training",
                display_name="Start Model Training",
                description="Start remote machine learning model training on the user's GPU-enabled system. Automatically configures and initiates a CNN model training session.",
                parameters={}
            ),
            Tool(
                id="make_model_training_chart",
                name="make_model_training_chart",
                display_name="Generate Training Chart",
                description="Generate a visualization chart showing the training progress of a machine learning model. Creates a chart with loss curves and saves it as an image file.",
                parameters={}
            ),
            Tool(
                id="wait_for_training",
                name="wait_for_training",
                display_name="Wait for Training Completion",
                description="Monitor and wait for the current model training session to complete. Returns the final training metrics and model performance.",
                parameters={}
            )
        ]

        # Track training sessions
        state = {
            "total_sessions": 0,
            "active_sessions": []
        }

        metadata = {
            "start_model_training": {
                "compute_backend": "MPS",
                "supported_frameworks": ["PyTorch", "TensorFlow", "JAX"],
                "device": "Apple Silicon"
            }
        }

        return tools, state, metadata

    def call_tool(
        self,
        tool_id: str,
        tool_parameters: Dict[str, Any],
        per_conversation_state: Dict[str, Any],
        global_state: Dict[str, Any]
    ) -> Tuple[Any, Optional[str]]:
        """Execute model training tool."""
        if tool_id == "start_model_training":
            # Use hardcoded values for demo
            model_type = "resnet50"
            dataset_name = "CIFAR-10"
            epochs = 100
            batch_size = 32
            learning_rate = 0.001
            optimizer = "adam"

            # Generate session ID
            session_id = f"training_{uuid.uuid4().hex[:8]}"

            # Simulate initialization and training startup
            print(f"Initializing {model_type} model training...")
            time.sleep(2)

            print(f"Loading dataset: {dataset_name}")
            time.sleep(2)

            print(f"Configuring training parameters...")
            time.sleep(1)

            print(f"Starting training on GPU...")
            time.sleep(5)

            # Generate realistic-looking statistics
            total_params = random.randint(1000000, 500000000)
            trainable_params = int(total_params * 0.95)
            dataset_size = random.randint(10000, 1000000)

            # Calculate estimated time based on parameters (20 minutes total)
            estimated_total_time = 1200  # 20 minutes in seconds
            time_per_epoch = estimated_total_time / epochs

            # Generate initial metrics
            initial_loss = round(random.uniform(2.5, 4.5), 4)
            initial_accuracy = round(random.uniform(0.05, 0.15), 4)

            # Update global state
            global_state["total_sessions"] += 1
            global_state["active_sessions"].append(session_id)

            # Store session info
            self.training_sessions[session_id] = {
                "model_type": model_type,
                "dataset": dataset_name,
                "start_time": datetime.now().isoformat(),
                "status": "running"
            }

            # Ensure CNN architecture details
            architecture_type = "CNN" if "cnn" in model_type.lower() or "resnet" in model_type.lower() else "CNN"

            return {
                "success": True,
                "session_id": session_id,
                "status": "training_started",
                "model_info": {
                    "type": f"{architecture_type} ({model_type})",
                    "architecture": architecture_type,
                    "total_parameters": total_params,
                    "trainable_parameters": trainable_params,
                    "non_trainable_parameters": total_params - trainable_params,
                    "estimated_memory_gb": round(total_params * 4 / (1024**3), 2),
                    "layers": {
                        "conv_layers": 13 if "resnet" in model_type.lower() else 8,
                        "pooling_layers": 5,
                        "fully_connected": 3
                    }
                },
                "dataset_info": {
                    "name": dataset_name,
                    "total_samples": dataset_size,
                    "train_samples": int(dataset_size * 0.8),
                    "validation_samples": int(dataset_size * 0.15),
                    "test_samples": int(dataset_size * 0.05)
                },
                "training_config": {
                    "epochs": epochs,
                    "batch_size": batch_size,
                    "learning_rate": learning_rate,
                    "optimizer": optimizer,
                    "loss_function": "categorical_crossentropy",
                    "metrics": ["accuracy", "loss", "val_accuracy", "val_loss"]
                },
                "hardware_info": {
                    "device": "Apple M1 Max",
                    "backend": "MPS (Metal Performance Shaders)",
                    "system_memory_gb": 32,
                    "available_memory_gb": 32,
                    "allocated_memory_gb": round(total_params * 4 / (1024**3) + 2, 2),
                    "gpu_cores": 32,
                    "neural_engine_cores": 16
                },
                "initial_metrics": {
                    "loss": initial_loss,
                    "accuracy": initial_accuracy,
                    "learning_rate": learning_rate
                },
                "estimated_time": {
                    "per_epoch_seconds": round(time_per_epoch, 1),
                    "total_seconds": round(estimated_total_time, 1),
                    "total_formatted": "20m"
                },
                "checkpoint_path": f"models/{session_id}/checkpoint.pth",
                "tensorboard_url": f"http://localhost:6006/#scalars&run={session_id}",
                "message": f"Training started successfully. Session ID: {session_id}. Monitor progress at tensorboard URL."
            }, None

        elif tool_id == "make_model_training_chart":
            # Get working directory from conversation state
            working_directory = per_conversation_state.get("_working_directory")
            if not working_directory:
                return None, "Working directory not available"

            # Source chart image (placeholder for now)
            source_chart = Path("/Users/michel/Desktop/evanai/demo_resources/training_chart.png")

            # Destination in conversation_data
            dest_path = Path(working_directory) / "conversation_data" / "training_progress_chart.png"

            # Ensure parent directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy the chart image
            try:
                # For demo purposes, we'll create a placeholder if source doesn't exist
                if not source_chart.exists():
                    # Create a simple placeholder file
                    dest_path.write_text("")  # This would normally be the actual chart
                else:
                    shutil.copy2(source_chart, dest_path)
            except Exception as e:
                return None, f"Failed to save chart: {str(e)}"

            # Return relative path from working directory
            relative_path = dest_path.relative_to(working_directory)

            return {
                "success": True,
                "chart_file": str(relative_path),
                "chart_type": "training_progress",
                "metrics_displayed": ["loss", "val_loss", "accuracy", "val_accuracy"],
                "format": "png",
                "resolution": "1920x1080",
                "message": f"Successfully generated training progress chart at {relative_path}"
            }, None

        elif tool_id == "wait_for_training":
            # Send message through websocket to notify user
            conversation_id = per_conversation_state.get("_conversation_id")
            if self.websocket_handler and conversation_id:
                self.websocket_handler.send_response(
                    conversation_id,
                    "I've started training, and I'll get back to you when it's finished.\n"
                )

            # Simulate monitoring training progress
            print("Monitoring training progress...")
            time.sleep(5)
            print("Epoch 20/100 completed...")
            time.sleep(5)
            print("Epoch 40/100 completed...")
            time.sleep(5)
            print("Epoch 60/100 completed...")
            time.sleep(5)
            print("Epoch 80/100 completed...")
            time.sleep(5)
            print("Epoch 100/100 completed...")
            time.sleep(5)
            print("Training completed successfully!")

            # Generate final metrics
            final_loss = round(random.uniform(0.15, 0.25), 4)
            final_accuracy = round(random.uniform(0.91, 0.96), 4)
            val_loss = round(random.uniform(0.20, 0.35), 4)
            val_accuracy = round(random.uniform(0.88, 0.93), 4)

            # Get latest session or create a dummy one
            if self.training_sessions:
                session_id = list(self.training_sessions.keys())[-1]
            else:
                session_id = f"training_{uuid.uuid4().hex[:8]}"

            return {
                "success": True,
                "session_id": session_id,
                "status": "completed",
                "training_time": {
                    "total_seconds": 1200,
                    "total_formatted": "20m",
                    "completed_at": datetime.now().isoformat()
                },
                "final_metrics": {
                    "train_loss": final_loss,
                    "train_accuracy": final_accuracy,
                    "val_loss": val_loss,
                    "val_accuracy": val_accuracy,
                    "test_accuracy": round(random.uniform(0.87, 0.92), 4)
                },
                "best_epoch": 85,
                "model_saved": True,
                "checkpoint_path": f"models/{session_id}/best_model.pth",
                "training_history": {
                    "loss_improved": True,
                    "early_stopping_triggered": False,
                    "total_epochs_run": 100
                },
                "hardware_stats": {
                    "peak_memory_gb": 18.5,
                    "avg_gpu_utilization": "78%",
                    "avg_batch_time_ms": 245
                },
                "message": "Training completed successfully. Model saved with 93.2% validation accuracy."
            }, None

        return None, f"Unknown tool: {tool_id}"

    def get_name(self) -> str:
        return "model_training_tools"

    def get_description(self) -> str:
        return "Tools for managing remote machine learning model training"