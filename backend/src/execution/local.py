import subprocess
import sys
import os
from typing import Dict, Any, Optional
from .base import ToolExecutor

class LocalExecutor(ToolExecutor):
    """
    Executes code locally. 
    WARNING: This provides NO sandboxing. Use only in trusted environments or for testing.
    """
    
    def execute(self, code: str, timeout: int = 30, env: Optional[Dict[str, str]] = None) -> str:
        # Create a temporary file to run the code
        # Ideally we'd use something like 'python -c' but for multi-line scripts file is safer
        import tempfile
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_path = f.name
                
            # Prepare environment
            run_env = os.environ.copy()
            if env:
                run_env.update(env)
            
            # Execute
            result = subprocess.run(
                [sys.executable, temp_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                env=run_env
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\n[STDERR]\n{result.stderr}"
                
            return output
            
        except subprocess.TimeoutExpired:
            return f"Error: Execution timed out after {timeout} seconds."
        except Exception as e:
            return f"Error executing code: {str(e)}"
        finally:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.unlink(temp_path)

    def cleanup(self):
        pass
