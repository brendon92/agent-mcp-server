import pytest
import asyncio
import tempfile
import pathlib
from unittest.mock import MagicMock, AsyncMock
from backend.src.registry import ToolRegistry, ToolNotFoundError, ToolExecutionError

@pytest.fixture
def mock_workspace():
    workspace = MagicMock()
    workspace.tools_path = pathlib.Path(tempfile.mkdtemp())
    workspace.get_tool_path = lambda name: workspace.tools_path / f"{name}.py"
    return workspace

@pytest.fixture
def registry(mock_workspace):
    return ToolRegistry(mock_workspace)

def test_tool_not_found_error(registry):
    with pytest.raises(ToolNotFoundError):
        asyncio.run(registry.call_tool("nonexistent_tool", {}))

def test_register_system_tool(registry):
    def dummy_tool(x: int) -> int:
        return x * 2
    
    registry.register_system_tool("test_tool", dummy_tool)
    assert "test_tool" in registry.system_tools

def test_call_system_tool(registry):
    def add(a: int, b: int) -> int:
        return a + b
    
    registry.register_system_tool("add", add)
    result = asyncio.run(registry.call_tool("add", {"a": 2, "b": 3}))
    assert result == 5

def test_list_tools(registry):
    def tool1():
        pass
    def tool2():
        pass
    
    registry.register_system_tool("tool1", tool1)
    registry.register_system_tool("tool2", tool2)
    
    tools = registry.list_tools()
    names = [t["name"] for t in tools]
    assert "tool1" in names
    assert "tool2" in names

def test_delete_nonexistent_tool(registry):
    with pytest.raises(ToolNotFoundError):
        registry.delete_dynamic_tool("nonexistent")
