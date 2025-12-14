from ..base import MCPIntegration
from ...utils.subprocess_mgmt import SubprocessManager
from typing import Dict, Any, List

class GitIngestIntegration(MCPIntegration):
    """Git Ingest integration for analyzing GitHub repositories."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.category = "vcs"
        self.name = "git_ingest"
        self.manager = None
        
    async def initialize(self) -> None:
        # Start the git-ingest MCP server via uvx
        cmd = self.config.get("args", ["uvx", "mcp-git-ingest"])
        self.manager = SubprocessManager(cmd)
        try:
            self.manager.start()
            print("Git Ingest integration started.")
        except Exception as e:
            print(f"Failed to start Git Ingest integration: {e}")
            self.manager = None
    
    async def shutdown(self) -> None:
        if self.manager:
            self.manager.stop()
    
    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "github_analyze",
                "description": "Analyze a GitHub repository structure and content",
                "category": "vcs",
                "integration": "git_ingest",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "repo_url": {"type": "string", "description": "GitHub repository URL"},
                        "branch": {"type": "string", "description": "Branch to analyze (default: main)"},
                        "include_patterns": {"type": "array", "items": {"type": "string"}, "description": "File patterns to include"},
                        "exclude_patterns": {"type": "array", "items": {"type": "string"}, "description": "File patterns to exclude"}
                    },
                    "required": ["repo_url"]
                }
            },
            {
                "name": "github_read_file",
                "description": "Read a specific file from a GitHub repository",
                "category": "vcs",
                "integration": "git_ingest",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "repo_url": {"type": "string", "description": "GitHub repository URL"},
                        "file_path": {"type": "string", "description": "Path to the file within the repository"},
                        "branch": {"type": "string", "description": "Branch to read from (default: main)"}
                    },
                    "required": ["repo_url", "file_path"]
                }
            },
            {
                "name": "github_list_files",
                "description": "List files in a GitHub repository directory",
                "category": "vcs",
                "integration": "git_ingest",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "repo_url": {"type": "string", "description": "GitHub repository URL"},
                        "directory": {"type": "string", "description": "Directory path (default: root)"},
                        "branch": {"type": "string", "description": "Branch to list from (default: main)"}
                    },
                    "required": ["repo_url"]
                }
            }
        ]
    
    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        if not self.manager:
            return "Error: Git Ingest integration is not running."
            
        # Map tool names to the underlying MCP server tool names
        tool_mapping = {
            "github_analyze": "ingest",
            "github_read_file": "read_file",
            "github_list_files": "list_files"
        }
        
        external_name = tool_mapping.get(tool_name, tool_name)
        
        return await self.manager.send_request("tools/call", {
            "name": external_name,
            "arguments": args
        })
