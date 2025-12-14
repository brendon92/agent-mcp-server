import os
import shutil
import subprocess
import stat
import logging
from typing import List, Dict, Any, Union
from backend.src.integrations.base import MCPIntegration
from backend.src.utils.security import BoxedPath, atomic_writer, SecurityError

logger = logging.getLogger(__name__)

# Allowed chmod modes (no setuid/setgid/sticky)
SAFE_MODES = {
    0o400, 0o440, 0o444,  # read-only
    0o600, 0o640, 0o644,  # owner write
    0o700, 0o750, 0o755,  # owner execute
    0o770, 0o775, 0o777,  # group/all execute
}

class FileSystemIntegration(MCPIntegration):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "filesystem"
        self.category = "system"
        self.root_dir = config.get("root_dir", os.getcwd())
        logger.info(f"FileSystemIntegration initialized with root: {self.root_dir}")

    async def initialize(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "list_directory",
                "description": "List files and directories in a path.",
                "input_schema": {"type": "object", "properties": {"path": {"type": "string", "default": "."}}}
            },
            {
                "name": "read_file",
                "description": "Read the contents of a file.",
                "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}
            },
            {
                "name": "write_file",
                "description": "Write content to a file atomically.",
                "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}
            },
            {
                "name": "delete_file",
                "description": "Delete a file securely.",
                "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}
            },
            {
                "name": "search_files",
                "description": "Search for files matching a pattern.",
                "input_schema": {"type": "object", "properties": {"query": {"type": "string"}, "path": {"type": "string", "default": "."}}, "required": ["query"]}
            },
            {
                "name": "mkdir",
                "description": "Create a directory securely.",
                "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "parents": {"type": "boolean", "default": False}}, "required": ["path"]}
            },
            {
                "name": "copy_file",
                "description": "Copy a file securely.",
                "input_schema": {"type": "object", "properties": {"src": {"type": "string"}, "dest": {"type": "string"}}, "required": ["src", "dest"]}
            },
            {
                "name": "move_file",
                "description": "Move/rename a file securely.",
                "input_schema": {"type": "object", "properties": {"src": {"type": "string"}, "dest": {"type": "string"}}, "required": ["src", "dest"]}
            },
            {
                "name": "append_file",
                "description": "Append content to a file atomically.",
                "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}
            },
            {
                "name": "chmod_file",
                "description": "Change file permissions (restricted modes only).",
                "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "mode": {"type": "integer"}}, "required": ["path", "mode"]}
            }
        ]

    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        logger.info(f"AUDIT: Tool '{tool_name}' called with args: {args}")
        
        try:
            if tool_name == "list_directory":
                return self._list_directory(args.get("path", "."))
            elif tool_name == "read_file":
                return self._read_file(args["path"])
            elif tool_name == "write_file":
                return self._write_file(args["path"], args["content"])
            elif tool_name == "delete_file":
                return self._delete_file(args["path"])
            elif tool_name == "search_files":
                return self._search_files(args["query"], args.get("path", "."))
            elif tool_name == "mkdir":
                return self._mkdir(args["path"], args.get("parents", False))
            elif tool_name == "copy_file":
                return self._copy_file(args["src"], args["dest"])
            elif tool_name == "move_file":
                return self._move_file(args["src"], args["dest"])
            elif tool_name == "append_file":
                return self._append_file(args["path"], args["content"])
            elif tool_name == "chmod_file":
                return self._chmod_file(args["path"], args["mode"])
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
        except SecurityError as e:
            logger.warning(f"SECURITY AUDIT: Violation in {tool_name}: {e}")
            return f"Error: Access Denied - {str(e)}"
        except Exception as e:
            logger.error(f"Error executing {tool_name}: {e}")
            return f"Error: {str(e)}"

    def _list_directory(self, path: str) -> Union[List[str], str]:
        boxed = BoxedPath(path, self.root_dir)
        if not boxed.is_dir():
            return f"Error: Not a directory: {path}"
        return os.listdir(boxed.full_path)

    def _read_file(self, path: str) -> str:
        boxed = BoxedPath(path, self.root_dir)
        if not boxed.is_file():
            return f"Error: Not a file: {path}"
        with open(boxed.full_path, "r", encoding="utf-8") as f:
            return f.read()

    def _write_file(self, path: str, content: str) -> str:
        boxed = BoxedPath(path, self.root_dir)
        with atomic_writer(boxed, mode="w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {path}"

    def _delete_file(self, path: str) -> str:
        boxed = BoxedPath(path, self.root_dir)
        if not boxed.is_file():
            return f"Error: Not a file: {path}"
        if str(boxed.full_path) == str(self.root_dir):
            raise SecurityError("Cannot delete root directory")
        os.remove(boxed.full_path)
        return f"Successfully deleted {path}"

    def _search_files(self, query: str, path: str) -> Union[List[str], str]:
        boxed = BoxedPath(path, self.root_dir)
        if not boxed.is_dir():
            return f"Error: Search path is not a directory: {path}"
        cmd = ["find", str(boxed.full_path), "-name", query]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        lines = [l for l in result.stdout.strip().split("\n") if l]
        return [os.path.relpath(p, self.root_dir) for p in lines][:100]

    def _mkdir(self, path: str, parents: bool = False) -> str:
        boxed = BoxedPath(path, self.root_dir)
        boxed.mkdir(parents=parents, exist_ok=True)
        return f"Successfully created directory {path}"

    def _copy_file(self, src: str, dest: str) -> str:
        src_boxed = BoxedPath(src, self.root_dir)
        dest_boxed = BoxedPath(dest, self.root_dir)
        if not src_boxed.is_file():
            return f"Error: Source is not a file: {src}"
        shutil.copy2(str(src_boxed.full_path), str(dest_boxed.full_path))
        return f"Successfully copied {src} to {dest}"

    def _move_file(self, src: str, dest: str) -> str:
        src_boxed = BoxedPath(src, self.root_dir)
        dest_boxed = BoxedPath(dest, self.root_dir)
        if not src_boxed.exists():
            return f"Error: Source does not exist: {src}"
        os.replace(str(src_boxed.full_path), str(dest_boxed.full_path))
        return f"Successfully moved {src} to {dest}"

    def _append_file(self, path: str, content: str) -> str:
        boxed = BoxedPath(path, self.root_dir)
        existing = ""
        if boxed.is_file():
            with open(boxed.full_path, "r", encoding="utf-8") as f:
                existing = f.read()
        with atomic_writer(boxed, mode="w", encoding="utf-8") as f:
            f.write(existing + content)
        return f"Successfully appended to {path}"

    def _chmod_file(self, path: str, mode: int) -> str:
        boxed = BoxedPath(path, self.root_dir)
        if not boxed.exists():
            return f"Error: Path does not exist: {path}"
        if mode not in SAFE_MODES:
            raise SecurityError(f"Mode {oct(mode)} not allowed. Safe modes: {[oct(m) for m in SAFE_MODES]}")
        os.chmod(str(boxed.full_path), mode)
        return f"Successfully changed permissions of {path} to {oct(mode)}"

