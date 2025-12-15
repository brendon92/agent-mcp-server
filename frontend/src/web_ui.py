import asyncio
import sys
import os
import uuid
import signal
import subprocess
from datetime import datetime, UTC
from typing import Dict, Any, List, Optional
import psutil
import secrets
import json
import threading
from enum import Enum
from pydantic import BaseModel
from fastapi import FastAPI, WebSocket, HTTPException, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.src.workspace import Workspace
from backend.src.registry import ToolRegistry
from backend.src.config.settings import ServerConfig

# Load Configuration
# Build absolute path relative to this module's location
# This file is at frontend/src/web_ui.py, backend config is at backend/config/
_module_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_module_dir))
_config_path = os.path.join(_project_root, "backend", "config", "workspace_config.yaml")
config = ServerConfig.from_yaml(_config_path)
workspace = Workspace(config.workspace_dir)
registry = ToolRegistry(workspace, config)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    await registry.load_integrations()
    # Note: sync_server_state() will be called after ServerState class is defined
    # This is handled by calling it when the app starts serving requests
    yield
    # Shutdown (if needed)
    pass

# Create FastAPI app
app = FastAPI(title="MCP Server Web UI", version="1.0.0", lifespan=lifespan)

# Task tracking
active_tasks: Dict[str, Dict[str, Any]] = {}
task_history: List[Dict[str, Any]] = []
MAX_HISTORY = 100

# Event queue for WebSocket broadcasting
active_websocket_connections: List[WebSocket] = []

# Server state management
class ServerState(str, Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"

mcp_server_process: Optional[subprocess.Popen] = None
mcp_server_state: ServerState = ServerState.STOPPED
stop_attempts: int = 0
external_server_pid: Optional[int] = None  # PID of externally started server

# PID file location (shared with backend)
PID_FILE = os.path.join(_project_root, ".mcp_server.pid")

# Authentication
AUTH_TOKEN = os.environ.get("MCP_AUTH_TOKEN")
if not AUTH_TOKEN:
    AUTH_TOKEN = secrets.token_urlsafe(32)
    print(f"\n{'='*60}\nWARNING: MCP_AUTH_TOKEN not set. Generated temporary token:\n{AUTH_TOKEN}\n{'='*60}\n")

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != AUTH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

# Web UI PID file for single instance check
WEB_UI_PID_FILE = os.path.join(_project_root, ".mcp_web_ui.pid")

def check_web_ui_single_instance():
    """Ensure only one Web UI instance is running.
    If another instance is detected, print error and exit."""
    if os.path.exists(WEB_UI_PID_FILE):
        try:
            with open(WEB_UI_PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            
            if psutil.pid_exists(pid):
                try:
                    proc = psutil.Process(pid)
                    cmdline = ' '.join(proc.cmdline())
                    if 'web_ui.py' in cmdline:
                        print(f"Error: MCP Web UI is already running (PID: {pid})", file=sys.stderr)
                        print(f"Kill it with: kill {pid}", file=sys.stderr)
                        sys.exit(1)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except (ValueError, FileNotFoundError):
            pass
    
    # Write our PID (lock acquired)
    try:
        with open(WEB_UI_PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
    except Exception as e:
        print(f"Warning: Could not write Web UI PID file: {e}", file=sys.stderr)

def cleanup_web_ui_pid_file():
    """Remove Web UI PID file on shutdown"""
    try:
        if os.path.exists(WEB_UI_PID_FILE):
            os.remove(WEB_UI_PID_FILE)
    except:
        pass

import atexit
atexit.register(cleanup_web_ui_pid_file)

def is_mcp_server_running() -> tuple:
    """Check if MCP server is already running.
    Returns (is_running, pid)"""
    # Method 1: Check PID file
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            if psutil.pid_exists(pid):
                try:
                    proc = psutil.Process(pid)
                    cmdline = ' '.join(proc.cmdline())
                    if 'server.py' in cmdline:
                        return (True, pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except (ValueError, FileNotFoundError, PermissionError):
            pass
    
    # Method 2: Scan all processes for server.py
    for proc in psutil.process_iter(['pid', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if 'backend/src/server.py' in cmdline or 'backend\\src\\server.py' in cmdline:
                return (True, proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return (False, None)

def sync_server_state():
    """Synchronize internal state with actual running state.
    Call this to detect externally started servers."""
    global mcp_server_state, mcp_server_process, external_server_pid
    
    # If we already have a process we're managing, check if it's still running
    if mcp_server_process is not None:
        if mcp_server_process.poll() is None:
            # Our managed process is still running
            mcp_server_state = ServerState.RUNNING
            return True
        else:
            # Our managed process has died
            mcp_server_process = None
    
    # Check for any running MCP server (including external)
    is_running, pid = is_mcp_server_running()
    
    if is_running:
        mcp_server_state = ServerState.RUNNING
        external_server_pid = pid
        return True
    
    mcp_server_state = ServerState.STOPPED
    external_server_pid = None
    return False

def log_reader(pipe, pipe_name):
    """Read lines from a pipe and emit them as events"""
    try:
        with pipe:
            for line in iter(pipe.readline, ''):
                # We need to use a loop to run the async emit_event in the main event loop
                # This is a bit tricky from a thread. 
                # For now, let's just print to stdout which will be captured by the system logs
                # and maybe add a proper async bridge later if we want real-time logs in UI from this.
                # Just reading the line prevents the buffer from filling up.
                print(f"[MCP Server {pipe_name}] {line.strip()}")
    except Exception as e:
        print(f"Log reader error for {pipe_name}: {e}")


# Request/Response Models
class ToolExecuteRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = {}

class ToolExecuteResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Any] = None
    result: Optional[Any] = None
    error: Optional[str] = None

class LoginRequest(BaseModel):
    token: str

# Helper Functions
async def emit_event(event_type: str, data: Dict[str, Any]):
    """Emit an event to all connected WebSocket clients"""
    event = {
        "type": event_type,
        "timestamp": datetime.now(UTC).isoformat(),
        **data
    }
    
    # Broadcast to all connected clients
    disconnected_clients = []
    for websocket in active_websocket_connections:
        try:
            await websocket.send_json(event)
        except Exception as e:
            print(f"Error sending to WebSocket client: {e}")
            disconnected_clients.append(websocket)
    
    # Remove disconnected clients
    for ws in disconnected_clients:
        if ws in active_websocket_connections:
            active_websocket_connections.remove(ws)

async def execute_tool_with_tracking(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a tool and track its lifecycle"""
    task_id = str(uuid.uuid4())
    start_time = datetime.now(UTC)
    
    # Create task record
    task_record = {
        "task_id": task_id,
        "tool_name": tool_name,
        "arguments": args,
        "status": "running",
        "start_time": start_time.isoformat(),
        "end_time": None,
        "duration": None,
        "result": None,
        "error": None
    }
    
    active_tasks[task_id] = task_record
    
    # Emit started event
    await emit_event("task_started", {
        "task_id": task_id,
        "tool_name": tool_name,
        "arguments": args
    })
    
    try:
        # Execute the tool
        result = await registry.call_tool(tool_name, args)
        
        # Update task record
        end_time = datetime.now(UTC)
        duration = (end_time - start_time).total_seconds()
        
        task_record.update({
            "status": "completed",
            "end_time": end_time.isoformat(),
            "duration": duration,
            "result": str(result)[:500]  # Truncate large results
        })
        
        # Emit completed event
        await emit_event("task_completed", {
            "task_id": task_id,
            "tool_name": tool_name,
            "status": "completed",
            "result": str(result)[:500],
            "duration": duration
        })
        
        return {
            "task_id": task_id,
            "status": "completed",
            "result": result
        }
        
    except Exception as e:
        # Update task record
        end_time = datetime.now(UTC)
        duration = (end_time - start_time).total_seconds()
        
        task_record.update({
            "status": "failed",
            "end_time": end_time.isoformat(),
            "duration": duration,
            "error": str(e)
        })
        
        # Emit failed event
        await emit_event("task_failed", {
            "task_id": task_id,
            "tool_name": tool_name,
            "status": "failed",
            "error": str(e),
            "duration": duration
        })
        
        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(e)
        }
        
    finally:
        # Move to history
        if task_id in active_tasks:
            completed_task = active_tasks.pop(task_id)
            task_history.insert(0, completed_task)
            # Keep history limited
            if len(task_history) > MAX_HISTORY:
                task_history.pop()

# API Endpoints

# API Endpoints

@app.post("/api/login")
async def login(request: LoginRequest):
    """Login endpoint to validate token"""
    if request.token == AUTH_TOKEN:
        return {"access_token": AUTH_TOKEN, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/api/health", dependencies=[Depends(verify_token)])
async def health_check():
    """Health check endpoint - syncs with actual server state"""
    # Sync with actual running state
    sync_server_state()
    return {
        "status": mcp_server_state.value, 
        "timestamp": datetime.now(UTC).isoformat(),
        "pid": external_server_pid if mcp_server_process is None else (mcp_server_process.pid if mcp_server_process else None)
    }

@app.get("/api/tools", dependencies=[Depends(verify_token)])
async def get_tools():
    """Get list of all available tools"""
    tools = registry.list_tools()
    return {"tools": tools}

@app.post("/api/tools/execute", dependencies=[Depends(verify_token)])
async def execute_tool(request: ToolExecuteRequest):
    """Execute a tool"""
    result = await execute_tool_with_tracking(request.tool_name, request.arguments)
    return result

@app.get("/api/tasks", dependencies=[Depends(verify_token)])
async def get_tasks():
    """Get active and recent tasks"""
    return {
        "active": list(active_tasks.values()),
        "history": task_history[:20]  # Return last 20
    }

@app.post("/api/tasks/{task_id}/cancel", dependencies=[Depends(verify_token)])
async def cancel_task(task_id: str):
    """Cancel a specific task (placeholder - actual cancellation needs asyncio.Task integration)"""
    if task_id in active_tasks:
        # In a real implementation, we'd need to store asyncio.Task objects
        # and call task.cancel() on them
        return {"status": "cancelled", "task_id": task_id, "note": "Cancellation not fully implemented"}
    else:
        raise HTTPException(status_code=404, detail="Task not found or already completed")

@app.post("/api/tasks/cancel_all", dependencies=[Depends(verify_token)])
async def cancel_all_tasks():
    """Cancel all running tasks"""
    cancelled = list(active_tasks.keys())
    # In a real implementation, we'd cancel all running asyncio tasks
    return {"status": "cancelled", "count": len(cancelled), "note": "Cancellation not fully implemented"}

@app.get("/api/server/state", dependencies=[Depends(verify_token)])
async def get_server_state():
    """Get current MCP server state - syncs with actual running processes"""
    # Sync with actual running state
    sync_server_state()
    
    pid = None
    is_external = False
    if mcp_server_process is not None and mcp_server_process.poll() is None:
        pid = mcp_server_process.pid
    elif external_server_pid is not None:
        pid = external_server_pid
        is_external = True
    
    return {
        "state": mcp_server_state.value,
        "stop_attempts": stop_attempts,
        "pid": pid,
        "is_external": is_external
    }

@app.post("/api/server/start", dependencies=[Depends(verify_token)])
async def start_server():
    """Start the MCP server"""
    global mcp_server_process, mcp_server_state
    
    # First, sync with actual state to detect external servers
    sync_server_state()
    
    if mcp_server_state == ServerState.RUNNING:
        pid = external_server_pid if mcp_server_process is None else mcp_server_process.pid
        raise HTTPException(status_code=400, detail=f"Server is already running (PID: {pid})")
    
    if mcp_server_state == ServerState.STARTING:
        raise HTTPException(status_code=400, detail="Server is already starting")
    
    if mcp_server_state == ServerState.STOPPING:
        raise HTTPException(status_code=400, detail="Server is currently stopping")
    
    try:
        mcp_server_state = ServerState.STARTING
        
        # Start MCP server as subprocess
        # Use the backend startup script to ensure environment is correct
        start_script = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "backend", "start.sh")
        mcp_server_process = subprocess.Popen(
            ["/bin/bash", start_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            text=True,
            bufsize=1
        )
        
        # Start threads to consume output and prevent deadlock
        threading.Thread(target=log_reader, args=(mcp_server_process.stdout, "stdout"), daemon=True).start()
        threading.Thread(target=log_reader, args=(mcp_server_process.stderr, "stderr"), daemon=True).start()
        
        # Wait a bit to check if it started successfully
        await asyncio.sleep(2)
        
        if mcp_server_process.poll() is None:
            # Process is running
            mcp_server_state = ServerState.RUNNING
            await emit_event("server_started", {
                "pid": mcp_server_process.pid,
                "server_type": "MCP Server",
                "status": "running"
            })
            return {"status": "running", "pid": mcp_server_process.pid}
        else:
            # Process died immediately
            mcp_server_state = ServerState.STOPPED
            stderr = mcp_server_process.stderr.read().decode() if mcp_server_process.stderr else ""
            await emit_event("server_failed", {
                "server_type": "MCP Server",
                "error": stderr[:200]
            })
            raise HTTPException(status_code=500, detail=f"Server failed to start: {stderr}")
            
    except Exception as e:
        mcp_server_state = ServerState.STOPPED
        raise HTTPException(status_code=500, detail=f"Failed to start server: {str(e)}")

@app.post("/api/server/stop", dependencies=[Depends(verify_token)])
async def stop_server(force: bool = False):
    """Stop the MCP server (handles both managed and external processes)"""
    global mcp_server_process, mcp_server_state, stop_attempts, external_server_pid
    
    # Sync state first
    sync_server_state()
    
    if mcp_server_state == ServerState.STOPPED:
        raise HTTPException(status_code=400, detail="Server is already stopped")
    
    if mcp_server_state == ServerState.STARTING:
        raise HTTPException(status_code=400, detail="Cannot stop while server is starting")
    
    if mcp_server_state == ServerState.STOPPING and not force:
        raise HTTPException(status_code=400, detail="Server is already stopping")
    
    try:
        mcp_server_state = ServerState.STOPPING
        stop_attempts += 1
        
        # Determine which process to stop
        target_pid = None
        is_external = False
        
        if mcp_server_process is not None and mcp_server_process.poll() is None:
            target_pid = mcp_server_process.pid
        elif external_server_pid is not None:
            target_pid = external_server_pid
            is_external = True
        
        if target_pid is None:
            mcp_server_state = ServerState.STOPPED
            stop_attempts = 0
            return {"status": "stopped", "method": "no_process"}
        
        # Get the process handle
        try:
            proc = psutil.Process(target_pid)
        except psutil.NoSuchProcess:
            mcp_server_state = ServerState.STOPPED
            stop_attempts = 0
            external_server_pid = None
            mcp_server_process = None
            return {"status": "stopped", "method": "process_gone"}
        
        if force or stop_attempts >= 3:
            # Force kill after 3 attempts
            proc.kill()
            proc.wait(timeout=5)
            mcp_server_state = ServerState.STOPPED
            stop_attempts = 0
            external_server_pid = None
            if not is_external:
                mcp_server_process = None
            await emit_event("server_stopped", {
                "method": "forced",
                "server_type": "MCP Server",
                "pid": target_pid,
                "was_external": is_external,
                "attempts": stop_attempts,
                "status": "stopped"
            })
            return {"status": "stopped", "method": "forced", "pid": target_pid, "was_external": is_external}
        else:
            # Graceful shutdown
            proc.terminate()
            
            # Wait up to 5 seconds for graceful shutdown
            for i in range(5):
                await asyncio.sleep(1)
                if not proc.is_running():
                    mcp_server_state = ServerState.STOPPED
                    stop_attempts = 0
                    external_server_pid = None
                    if not is_external:
                        mcp_server_process = None
                    await emit_event("server_stopped", {
                        "method": "graceful",
                        "server_type": "MCP Server",
                        "pid": target_pid,
                        "was_external": is_external,
                        "status": "stopped"
                    })
                    return {"status": "stopped", "method": "graceful", "pid": target_pid, "was_external": is_external}
            
            # Still running, increment attempts
            mcp_server_state = ServerState.RUNNING
            return {"status": "stopping", "method": "graceful_pending", "attempts": stop_attempts}
            
    except Exception as e:
        mcp_server_state = ServerState.RUNNING
        raise HTTPException(status_code=500, detail=f"Failed to stop server: {str(e)}")

@app.post("/api/server/restart", dependencies=[Depends(verify_token)])
async def restart_server():
    """Restart the MCP server"""
    global stop_attempts
    
    if mcp_server_state == ServerState.STARTING:
        raise HTTPException(status_code=400, detail="Cannot restart while server is starting")
    
    if mcp_server_state == ServerState.STOPPING:
        raise HTTPException(status_code=400, detail="Cannot restart while server is stopping")
    
    try:
        # Stop if running (emits server_stopped event)
        if mcp_server_state == ServerState.RUNNING:
            stop_attempts = 0  # Reset for restart
            await stop_server(force=True)
        
        # Start (emits server_started event)
        result = await start_server()
        
        # Emit restart event
        await emit_event("server_restarted", {
            "server_type": "MCP Server",
            "status": "restarted",
            "note": "Stop and Start events also emitted"
        })
        return {"status": "restarted", **result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restart server: {str(e)}")

# WebSocket for real-time logs
@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket endpoint for real-time event streaming"""
    await websocket.accept()
    active_websocket_connections.append(websocket)
    
    try:
        # Send initial connection event
        await websocket.send_json({
            "type": "connection_established",
            "timestamp": datetime.now(UTC).isoformat(),
            "message": "Connected to event stream"
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            # Wait for messages from client (ping/pong)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_json({"type": "ping", "timestamp": datetime.now(UTC).isoformat()})
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        if websocket in active_websocket_connections:
            active_websocket_connections.remove(websocket)
        try:
            await websocket.close()
        except:
            pass

# Serve static files
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")



if __name__ == "__main__":
    import argparse
    import uvicorn
    
    # Check for existing instance before starting
    check_web_ui_single_instance()
    
    parser = argparse.ArgumentParser(description="MCP Server Web UI")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on (default: 8000)")
    args = parser.parse_args()
    
    uvicorn.run(app, host="0.0.0.0", port=args.port)
