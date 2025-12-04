import os
import pytest
import tempfile
import pathlib
import asyncio
from backend.src.integrations.filesystem.secure import FileSystemIntegration

@pytest.fixture
def fs_integration():
    with tempfile.TemporaryDirectory() as tmpdir:
        config = {"root_dir": tmpdir}
        integration = FileSystemIntegration(config)
        yield integration, pathlib.Path(tmpdir)

def test_list_directory(fs_integration):
    integration, root = fs_integration
    (root / "file1.txt").touch()
    (root / "subdir").mkdir()
    
    result = asyncio.run(integration.call_tool("list_directory", {"path": "."}))
    assert "file1.txt" in result
    assert "subdir" in result

def test_read_write_file(fs_integration):
    integration, root = fs_integration
    
    # Write
    asyncio.run(integration.call_tool("write_file", {"path": "test.txt", "content": "hello"}))
    assert (root / "test.txt").read_text() == "hello"
    
    # Read
    content = asyncio.run(integration.call_tool("read_file", {"path": "test.txt"}))
    assert content == "hello"

def test_delete_file(fs_integration):
    integration, root = fs_integration
    (root / "delete_me.txt").touch()
    
    asyncio.run(integration.call_tool("delete_file", {"path": "delete_me.txt"}))
    assert not (root / "delete_me.txt").exists()

def test_search_files(fs_integration):
    integration, root = fs_integration
    (root / "find_me.py").touch()
    (root / "ignore_me.txt").touch()
    
    result = asyncio.run(integration.call_tool("search_files", {"query": "*.py"}))
    assert "find_me.py" in result
    assert "ignore_me.txt" not in result

def test_security_violation(fs_integration):
    integration, root = fs_integration
    
    # Try to read outside
    result = asyncio.run(integration.call_tool("read_file", {"path": "../outside"}))
    assert "Access Denied" in result
