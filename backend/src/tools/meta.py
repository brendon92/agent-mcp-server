from ..registry import ToolRegistry

class MetaTools:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def create_tool(self, name: str, code: str, category: str = "User Defined") -> str:
        """Creates a new dynamic tool."""
        try:
            self.registry.create_dynamic_tool(name, code, category)
            return f"Successfully created tool '{name}' in category '{category}'"
        except Exception as e:
            return f"Error creating tool: {str(e)}"

    def delete_tool(self, name: str) -> str:
        """Deletes a dynamic tool."""
        try:
            self.registry.delete_dynamic_tool(name)
            return f"Successfully deleted tool '{name}'"
        except Exception as e:
            return f"Error deleting tool: {str(e)}"
