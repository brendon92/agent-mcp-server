from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import httpx
import uvicorn

app = FastAPI(title="MCP Gateway")

class MCPServer(BaseModel):
    name: str
    url: str
    token: Optional[str] = None

# In-memory registry of servers
registered_servers: Dict[str, MCPServer] = {}

class RegisterRequest(BaseModel):
    name: str
    url: str
    token: Optional[str] = None

@app.post("/api/gateway/register")
async def register_server(request: RegisterRequest):
    """Register a downstream MCP server"""
    server = MCPServer(name=request.name, url=request.url, token=request.token)
    registered_servers[request.name] = server
    return {"status": "registered", "name": request.name}

@app.get("/api/gateway/servers")
async def list_servers():
    """List all registered servers"""
    return {"servers": list(registered_servers.values())}

@app.get("/api/tools")
async def list_aggregated_tools():
    """Aggregate tools from all registered servers"""
    aggregated_tools = []
    
    async with httpx.AsyncClient() as client:
        for name, server in registered_servers.items():
            try:
                headers = {}
                if server.token:
                    headers["Authorization"] = f"Bearer {server.token}"
                
                response = await client.get(f"{server.url}/api/tools", headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    tools = data.get("tools", [])
                    # Namespace tools
                    for tool in tools:
                        tool["original_name"] = tool["name"]
                        tool["name"] = f"{name}.{tool['name']}"
                        tool["server"] = name
                        aggregated_tools.append(tool)
            except Exception as e:
                print(f"Failed to fetch tools from {name}: {e}")
                
    return {"tools": aggregated_tools}

class ExecuteRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = {}

@app.post("/api/tools/execute")
async def execute_tool(request: ExecuteRequest):
    """Route tool execution to the appropriate server"""
    if "." not in request.tool_name:
        raise HTTPException(status_code=400, detail="Tool name must be namespaced (server.tool)")
    
    server_name, tool_name = request.tool_name.split(".", 1)
    
    server = registered_servers.get(server_name)
    if not server:
        raise HTTPException(status_code=404, detail=f"Server '{server_name}' not found")
        
    async with httpx.AsyncClient() as client:
        headers = {}
        if server.token:
            headers["Authorization"] = f"Bearer {server.token}"
            
        payload = {
            "tool_name": tool_name,
            "arguments": request.arguments
        }
        
        try:
            response = await client.post(
                f"{server.url}/api/tools/execute",
                json=payload,
                headers=headers
            )
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to execute on downstream server: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
