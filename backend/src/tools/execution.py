import subprocess
import sys
from ..workspace import Workspace

class ExecutionTools:
    def __init__(self, workspace: Workspace):
        self.workspace = workspace

    def execute_python_code(self, code: str) -> str:
        """
        Executes Python code in a sandboxed environment.
        WARNING: This implementation uses a subprocess for MVP.
        For production, use Docker or a proper sandbox.
        """
        if not self.workspace.config.get("allow_execute_code", False):
            raise PermissionError("Code execution is disabled in this workspace.")

        # MVP: Run in a separate process
        # We pass the code via stdin
        try:
            result = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                timeout=10, # 10 second timeout
                cwd=str(self.workspace.files_path) # Run in workspace files dir
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR:\n{result.stderr}"
                
            return output
            
        except subprocess.TimeoutExpired:
            return "Error: Execution timed out."
        except Exception as e:
            return f"Error executing code: {str(e)}"
