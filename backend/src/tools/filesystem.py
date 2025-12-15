from ..workspace import Workspace

class FilesystemTools:
    def __init__(self, workspace: Workspace, on_change=None):
        self.workspace = workspace
        self.on_change = on_change

    def read_file(self, path: str) -> str:
        """Reads a file from the workspace."""
        full_path = self.workspace.validate_path(path)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        with open(full_path, "r") as f:
            return f.read()

    def write_file(self, path: str, content: str) -> str:
        """Writes content to a file in the workspace."""
        if not self.workspace.config.get("allow_create_files", False):
            raise PermissionError("File creation is disabled in this workspace.")
            
        full_path = self.workspace.validate_path(path)
        
        # Ensure parent dirs exist
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, "w") as f:
            f.write(content)
            
        # Notify
        if self.on_change:
            try:
                self.on_change(path)
            except Exception:
                pass # logging handled by caller
            
        return f"Successfully wrote to {path}"

    def delete_file(self, path: str) -> str:
        """Deletes a file from the workspace."""
        if not self.workspace.config.get("allow_delete_files", False):
            raise PermissionError("File deletion is disabled in this workspace.")
            
        full_path = self.workspace.validate_path(path)
        
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
            
        full_path.unlink()
        
        # Notify
        if self.on_change:
            try:
                self.on_change(path)
            except Exception:
                pass
                
        return f"Successfully deleted {path}"

    def list_files(self, path: str = ".") -> str:
        """Lists files in a directory within the workspace."""
        full_path = self.workspace.validate_path(path)
        
        if not full_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {path}")
            
        files = [p.name for p in full_path.iterdir()]
        return "\n".join(files)
