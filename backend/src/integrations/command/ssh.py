from ..base import MCPIntegration
from typing import Dict, Any, List
import asyncio

class SshIntegration(MCPIntegration):
    """SSH integration for remote command execution."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.category = "command"
        self.name = "ssh"
        self.connections: Dict[str, Any] = {}
        
    async def initialize(self) -> None:
        # SSH connections are established on-demand
        print("SSH integration initialized.")
    
    async def shutdown(self) -> None:
        # Close all connections
        for conn in self.connections.values():
            if hasattr(conn, 'close'):
                conn.close()
        self.connections.clear()
    
    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "ssh_execute",
                "description": "Execute a command on a remote host via SSH",
                "category": "command",
                "integration": "ssh",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "host": {"type": "string", "description": "Remote host address"},
                        "username": {"type": "string", "description": "SSH username"},
                        "command": {"type": "string", "description": "Command to execute"},
                        "port": {"type": "integer", "description": "SSH port (default 22)"},
                        "password": {"type": "string", "description": "SSH password (optional, use key-based auth if not provided)"},
                        "key_file": {"type": "string", "description": "Path to SSH private key file (optional)"}
                    },
                    "required": ["host", "username", "command"]
                }
            },
            {
                "name": "ssh_upload",
                "description": "Upload a file to a remote host via SCP/SFTP",
                "category": "command",
                "integration": "ssh",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "host": {"type": "string"},
                        "username": {"type": "string"},
                        "local_path": {"type": "string", "description": "Local file path"},
                        "remote_path": {"type": "string", "description": "Remote destination path"},
                        "port": {"type": "integer"},
                        "password": {"type": "string"},
                        "key_file": {"type": "string"}
                    },
                    "required": ["host", "username", "local_path", "remote_path"]
                }
            },
            {
                "name": "ssh_download",
                "description": "Download a file from a remote host via SCP/SFTP",
                "category": "command",
                "integration": "ssh",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "host": {"type": "string"},
                        "username": {"type": "string"},
                        "remote_path": {"type": "string", "description": "Remote file path"},
                        "local_path": {"type": "string", "description": "Local destination path"},
                        "port": {"type": "integer"},
                        "password": {"type": "string"},
                        "key_file": {"type": "string"}
                    },
                    "required": ["host", "username", "remote_path", "local_path"]
                }
            }
        ]
    
    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        try:
            import paramiko
        except ImportError:
            return "Error: paramiko package is required. Install with: pip install paramiko"
        
        host = args.get("host")
        username = args.get("username")
        port = args.get("port", 22)
        password = args.get("password")
        key_file = args.get("key_file")
        
        # Create SSH client
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # Connect
            connect_kwargs = {
                "hostname": host,
                "port": port,
                "username": username,
            }
            if key_file:
                connect_kwargs["key_filename"] = key_file
            elif password:
                connect_kwargs["password"] = password
            else:
                # Try default key locations
                connect_kwargs["look_for_keys"] = True
                
            await asyncio.to_thread(client.connect, **connect_kwargs)
            
            if tool_name == "ssh_execute":
                command = args.get("command")
                stdin, stdout, stderr = await asyncio.to_thread(client.exec_command, command)
                output = await asyncio.to_thread(stdout.read)
                error = await asyncio.to_thread(stderr.read)
                exit_code = stdout.channel.recv_exit_status()
                
                return {
                    "output": output.decode(),
                    "error": error.decode(),
                    "exit_code": exit_code
                }
                
            elif tool_name == "ssh_upload":
                sftp = await asyncio.to_thread(client.open_sftp)
                local_path = args.get("local_path")
                remote_path = args.get("remote_path")
                await asyncio.to_thread(sftp.put, local_path, remote_path)
                sftp.close()
                return f"Uploaded {local_path} to {host}:{remote_path}"
                
            elif tool_name == "ssh_download":
                sftp = await asyncio.to_thread(client.open_sftp)
                remote_path = args.get("remote_path")
                local_path = args.get("local_path")
                await asyncio.to_thread(sftp.get, remote_path, local_path)
                sftp.close()
                return f"Downloaded {host}:{remote_path} to {local_path}"
                
        except Exception as e:
            return f"SSH Error: {str(e)}"
        finally:
            client.close()
