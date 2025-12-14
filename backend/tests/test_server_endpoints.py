import pytest
import json
from backend.src.server import get_tools_by_category, search_tools, get_available_categories

def test_get_tools_by_category_structure():
    """Test that tools are correctly grouped by category"""
    result = get_tools_by_category()
    data = json.loads(result)
    assert isinstance(data, dict)
    assert "File Operations" in data
    assert "Browser Automation" in data
    
    # Check content of a category
    file_ops = data["File Operations"]
    assert isinstance(file_ops, list)
    assert any(t["name"] == "read_file" for t in file_ops)

def test_search_tools():
    """Test searching for tools"""
    # Search for a known tool
    result = search_tools("read_file")
    data = json.loads(result)
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["name"] == "read_file"
    
    # Search for non-existent tool
    result = search_tools("non_existent_tool_xyz")
    data = json.loads(result)
    assert isinstance(data, list)
    assert len(data) == 0

def test_get_available_categories():
    """Test retrieving available categories"""
    result = get_available_categories()
    data = json.loads(result)
    assert isinstance(data, dict)
    assert "File Operations" in data
    assert data["File Operations"] >= 4
