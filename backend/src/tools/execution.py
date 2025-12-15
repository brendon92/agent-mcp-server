from ..workspace import Workspace
from ..config.settings import ServerConfig
from ..execution.docker import DockerExecutor
from ..execution.local import LocalExecutor
import logging

logger = logging.getLogger(__name__)

class ExecutionTools:
    def __init__(self, workspace: Workspace, config: ServerConfig):
        self.workspace = workspace
        self.config = config
        self.executor: ToolExecutor = self._initialize_executor()

    def _initialize_executor(self):
        if self.config.sandbox_enabled:
            try:
                # Try Docker
                logger.info("Initializing DockerExecutor...")
                return DockerExecutor()
            except Exception as e:
                logger.warning(f"Failed to initialize DockerExecutor: {e}. Falling back to LocalExecutor.")
                return LocalExecutor()
        else:
            logger.info("Sandbox disabled. Using LocalExecutor.")
            return LocalExecutor()

    def execute_python_code(self, code: str) -> str:
        """
        Executes Python code using the configured executor.
        """
        # Security check (double check configuration)
        # Note: Pydantic settings are robust, but verification doesn't hurt.
        
        timeout = self.config.max_tool_execution_time
        
        # We can inject workspace path as env var if needed
        env = {"WORKSPACE_DIR": str(self.workspace.files_path)}
        
        return self.executor.execute(code, timeout=timeout, env=env)
