import json
import os
from pathlib import Path
from typing import Dict, Any

class Workspace:
    def __init__(self, workspace_path: str):
        self.root_path = Path(workspace_path).resolve()
        self.config_path = self.root_path / "config.json"
        self.tools_path = self.root_path / "tools"
        self.files_path = self.root_path / "files"
        
        self._ensure_directories()
        self.config = self._load_config()

    def _ensure_directories(self):
        self.root_path.mkdir(parents=True, exist_ok=True)
        self.tools_path.mkdir(exist_ok=True)
        self.files_path.mkdir(exist_ok=True)
        
        if not self.config_path.exists():
            default_config = {
                "allow_create_files": True,
                "allow_delete_files": False,
                "allow_execute_code": False
            }
            with open(self.config_path, "w") as f:
                json.dump(default_config, f, indent=4)

    def _load_config(self) -> Dict[str, Any]:
        with open(self.config_path, "r") as f:
            return json.load(f)

    def validate_path(self, path: str) -> Path:
        """
        Validates that a path is within the workspace's files directory.
        Returns the resolved absolute path.
        Raises ValueError if path is outside workspace.
        """
        # Handle absolute paths by stripping root if it matches, or treating as relative
        target_path = Path(path)
        if target_path.is_absolute():
            try:
                target_path = target_path.relative_to(self.files_path)
            except ValueError:
                # If it's absolute but not in files_path, treat as filename
                target_path = Path(path).name
        
        full_path = (self.files_path / target_path).resolve()
        
        if not str(full_path).startswith(str(self.files_path)):
            raise ValueError(f"Access denied: Path {path} is outside workspace.")
            
        return full_path

    def get_tool_path(self, tool_name: str) -> Path:
        """Returns the path to a dynamic tool script."""
        # Sanitize tool name to prevent traversal
        safe_name = Path(tool_name).name
        return self.tools_path / f"{safe_name}.py"
