import asyncio
import subprocess
import json
import os
from typing import List, Dict, Any, Optional

class SubprocessManager:
    def __init__(self, command: List[str], env: Optional[Dict[str, str]] = None, cwd: Optional[str] = None):
        self.command = command
        self.env = env or os.environ.copy()
        self.cwd = cwd
        self.process: Optional[subprocess.Popen] = None
        
    def start(self):
        """Start the subprocess."""
        try:
            self.process = subprocess.Popen(
                self.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=self.env,
                cwd=self.cwd,
                text=True, # Use text mode for easier JSON handling
                bufsize=1  # Line buffered
            )
        except Exception as e:
            raise RuntimeError(f"Failed to start subprocess {self.command}: {e}")

    def stop(self):
        """Terminate the subprocess."""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

    async def send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Send a JSON-RPC request to the subprocess and await response."""
        if not self.process:
            raise RuntimeError("Process not running")

        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": 1 # Simple ID for now
        }
        
        json_req = json.dumps(request)
        
        # Write request
        try:
            self.process.stdin.write(json_req + "\n")
            self.process.stdin.flush()
        except (BrokenPipeError, IOError):
             raise RuntimeError("Process stdin closed")

        # Read response
        # This is a blocking read, in a real async server we might want to use asyncio.create_subprocess_exec
        # But for this implementation we'll wrap it in a thread or assume fast response
        # For better async support, we should refactor this to use asyncio.subprocess
        
        return await asyncio.to_thread(self._read_response)

    def _read_response(self):
        if not self.process:
             return None
             
        line = self.process.stdout.readline()
        if not line:
            # Check stderr
            err = self.process.stderr.read()
            raise RuntimeError(f"Process exited or closed stdout. Stderr: {err}")
            
        try:
            response = json.loads(line)
            if "error" in response:
                raise RuntimeError(f"RPC Error: {response['error']}")
            return response.get("result")
        except json.JSONDecodeError:
             raise RuntimeError(f"Invalid JSON response: {line}")
