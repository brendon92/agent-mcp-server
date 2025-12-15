import os
import sys
import asyncio
import json
import logging
import atexit
from typing import Any, Dict
import psutil
from mcp.server.fastmcp import FastMCP

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.src.workspace import Workspace
from backend.src.registry import ToolRegistry
from backend.src.config.settings import ServerConfig
from backend.src.tools.filesystem import FilesystemTools
from backend.src.tools.execution import ExecutionTools
from backend.src.tools.meta import MetaTools
from backend.src.tools.time import TimeTools
from backend.src.tools.browser import BrowserTools

# Load Configuration
# Build absolute path relative to this module's location
_module_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_module_dir)
_config_path = os.path.join(_backend_dir, "config", "workspace_config.yaml")
config = ServerConfig.from_yaml(_config_path)

# PID file for server detection (shared with frontend web_ui.py)
_project_root = os.path.dirname(_backend_dir)
PID_FILE = os.path.join(_project_root, ".mcp_server.pid")

# Configure Logging
LOG_FILE = os.path.join(_project_root, "backend_server.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        # Note: We do NOT add StreamHandler here because mcp uses stdio for communication
        # and writing random logs to stdout/stderr might corrupt the JSON-RPC stream
        # if the client isn't handling stderr correctly.
        # But usually stderr is safe. Start with just file for safety.
    ]
)
logger = logging.getLogger("mcp_server")
logger.info("----------------------------------------------------------------")
logger.info(f"MCP Backend Server Starting. Log file: {LOG_FILE}")
logger.info(f"Project Root: {_project_root}")


def write_pid_file():
    """Write current process PID to file for detection by web UI"""
    try:
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
    except Exception as e:
        print(f"Warning: Could not write PID file: {e}", file=sys.stderr)

def cleanup_pid_file():
    """Remove PID file on shutdown"""
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    except Exception as e:
        print(f"Warning: Could not remove PID file: {e}", file=sys.stderr)

def check_single_instance():
    """Ensure only one MCP server instance is running.
    If another instance is detected, print error and exit."""
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            
            if psutil.pid_exists(pid):
                try:
                    proc = psutil.Process(pid)
                    cmdline = ' '.join(proc.cmdline())
                    # Check if it's actually our server
                    if 'server.py' in cmdline:
                        print(f"Error: MCP Server is already running (PID: {pid})", file=sys.stderr)
                        print(f"Kill it with: kill {pid}", file=sys.stderr)
                        sys.exit(1)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # Process died or we can't access it, assume stale lock
                    pass
        except (ValueError, FileNotFoundError):
            # Invalid file content, assume stale
            pass
    
    # Write our PID (lock acquired)
    write_pid_file()

# Register cleanup handler
atexit.register(cleanup_pid_file)

# Initialize Workspace
workspace = Workspace(config.workspace_dir)

# Initialize Registry and Tools
registry = ToolRegistry(workspace, config)
fs_tools = FilesystemTools(workspace)
exec_tools = ExecutionTools(workspace)
meta_tools = MetaTools(registry)
time_tools = TimeTools()
browser_tools = BrowserTools(workspace)

# Initialize MCP Server
mcp = FastMCP("My Custom MCP Server")

# --- Register System Tools with Categories ---
registry.register_system_tool("read_file", fs_tools.read_file, "File Operations")
registry.register_system_tool("write_file", fs_tools.write_file, "File Operations")
registry.register_system_tool("delete_file", fs_tools.delete_file, "File Operations")
registry.register_system_tool("list_files", fs_tools.list_files, "File Operations")

registry.register_system_tool("execute_python_code", exec_tools.execute_python_code, "Code Execution")

registry.register_system_tool("create_tool", meta_tools.create_tool, "Tool Management")
registry.register_system_tool("delete_tool", meta_tools.delete_tool, "Tool Management")

registry.register_system_tool("get_current_time", time_tools.get_current_time, "Utilities")

registry.register_system_tool("open_page", browser_tools.open_page, "Browser Automation")
registry.register_system_tool("get_content", browser_tools.get_content, "Browser Automation")
registry.register_system_tool("click", browser_tools.click, "Browser Automation")
registry.register_system_tool("type", browser_tools.type, "Browser Automation")
registry.register_system_tool("screenshot", browser_tools.screenshot, "Browser Automation")


# --- Expose Tools via FastMCP ---

# Filesystem
@mcp.tool()
def read_file(path: str) -> str:
    """Reads a file from the workspace."""
    return fs_tools.read_file(path)

@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Writes content to a file in the workspace."""
    return fs_tools.write_file(path, content)

@mcp.tool()
def delete_file(path: str) -> str:
    """Deletes a file from the workspace."""
    return fs_tools.delete_file(path)

@mcp.tool()
def list_files(path: str = ".") -> str:
    """Lists files in a directory within the workspace."""
    return fs_tools.list_files(path)

# Execution
@mcp.tool()
def execute_python_code(code: str) -> str:
    """Executes Python code in a sandboxed environment."""
    return exec_tools.execute_python_code(code)

# Meta (Tool Management)
@mcp.tool()
def create_tool(name: str, code: str, category: str = "User Defined") -> str:
    """Creates a new dynamic tool."""
    return meta_tools.create_tool(name, code, category)

@mcp.tool()
def delete_tool(name: str) -> str:
    """Deletes a dynamic tool."""
    return meta_tools.delete_tool(name)

# Time
@mcp.tool()
def get_current_time(format: str = "long", timezone: str = "UTC") -> str:
    """Gets the current time in a specific format and timezone."""
    return time_tools.get_current_time(format, timezone)

# Browser
@mcp.tool()
async def open_page(url: str) -> str:
    """Opens a URL in the browser."""
    return await browser_tools.open_page(url)

@mcp.tool()
async def get_page_content() -> str:
    """Gets the text content of the current page."""
    return await browser_tools.get_content()

@mcp.tool()
async def click_element(selector: str) -> str:
    """Clicks an element matching the selector."""
    return await browser_tools.click(selector)

@mcp.tool()
async def type_text(selector: str, text: str) -> str:
    """Types text into an element matching the selector."""
    return await browser_tools.type(selector, text)

@mcp.tool()
async def take_screenshot(filename: str) -> str:
    """Takes a screenshot and saves it to the workspace."""
    return await browser_tools.screenshot(filename)


# --- Dynamic Tool Loading ---
registry.load_dynamic_tools()

@mcp.tool()
def call_dynamic_tool(name: str, args: str = "{}") -> str:
    """Calls a dynamically created tool."""
    try:
        tool_info = registry.dynamic_tools.get(name)
        if not tool_info:
            registry.load_dynamic_tools()
            tool_info = registry.dynamic_tools.get(name)
            
        if not tool_info:
            return f"Tool '{name}' not found."
            
        tool_code = tool_info["code"]
        
        parsed_args = json.loads(args)
        args_code = f"args = {json.dumps(parsed_args)}\n"
        full_code = args_code + tool_code
        
        return exec_tools.execute_python_code(full_code)
        
    except Exception as e:
        return f"Error calling dynamic tool: {str(e)}"

# --- Tool Discovery APIs ---

@mcp.tool()
def get_tools_by_category(category: str = None) -> str:
    """
    Get tools organized by category.
    
    Args:
        category: Filter by specific category (optional)
    
    Returns:
        JSON structure of tools grouped by category
    """
    all_tools = registry.list_tools()
    
    if category:
        tools = [t for t in all_tools if t["category"] == category]
    else:
        tools = all_tools
    
    # Group by category
    by_category = {}
    for tool in tools:
        cat = tool["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(tool)
    
    return json.dumps(by_category, indent=2)

@mcp.tool()
def search_tools(query: str) -> str:
    """
    Search for tools by name or description.
    
    Args:
        query: Search term
    
    Returns:
        List of matching tools
    """
    all_tools = registry.list_tools()
    query_lower = query.lower()
    
    matches = [
        t for t in all_tools
        if query_lower in t["name"].lower() 
        or query_lower in t.get("description", "").lower()
    ]
    
    return json.dumps(matches, indent=2)

@mcp.tool()
def get_available_categories() -> str:
    """List all tool categories with counts"""
    all_tools = registry.list_tools()
    
    categories = {}
    for tool in all_tools:
        cat = tool["category"]
        categories[cat] = categories.get(cat, 0) + 1
    
    return json.dumps(categories, indent=2)

@mcp.tool()
def get_tool_list() -> str:
    """Returns a JSON list of all tools with their categories."""
    return json.dumps(registry.list_tools(), indent=2)

# --- Integration Loading ---

async def load_integrations_and_register():
    await registry.load_integrations()
    
    for tool_def in registry.list_tools():
        if tool_def["type"] == "integration":
            create_mcp_tool_wrapper(mcp, tool_def, registry)

def create_mcp_tool_wrapper(mcp_instance, tool_def, tool_registry):
    """Create FastMCP wrapper for integrated tools"""
    tool_name = tool_def["name"]
    
    @mcp_instance.tool(name=tool_name)
    async def wrapper(**kwargs):
        return await tool_registry.call_tool(tool_name, kwargs)
    
    wrapper.__name__ = tool_name
    wrapper.__doc__ = tool_def.get("description", "")
    
    # We need to manually register it because the decorator might not work 
    # if called after mcp creation but before run? 
    # FastMCP collects tools via the decorator.
    # Since we are calling this before mcp.run(), it should work.

if __name__ == "__main__":
    async def main():
        # Check for existing instance and acquire lock
        check_single_instance()
        
        # Load integrations
        await load_integrations_and_register()
        
        # Run MCP server
        # run_stdio_async runs the server over stdio
        await mcp.run_stdio_async()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)
