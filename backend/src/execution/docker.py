import docker
import tarfile
import io
import os
from typing import Dict, Any, Optional
from .base import ToolExecutor

class DockerExecutor(ToolExecutor):
    """
    Executes code inside a Docker container.
    """
    
    def __init__(self, image: str = "python:3.11-slim"):
        self.client = docker.from_env()
        self.image = image
        # Ensure image exists
        try:
            self.client.images.get(image)
        except docker.errors.ImageNotFound:
            print(f"Pulling sandbox image: {image}...")
            self.client.images.pull(image)

    def execute(self, code: str, timeout: int = 30, env: Optional[Dict[str, str]] = None) -> str:
        container = None
        try:
            # We run the container in detached mode with 'sleep infinity' 
            # or just run the command directly?
            # Running directly is safer for "one-shot" execution.
            
            # Create a simple wrapper to execute the string code
            # Note: escaping quotes in 'python -c' is hard.
            # Better to write script to file inside container.
            
            # 1. Start container
            container = self.client.containers.run(
                self.image,
                command="sleep 300", # Keep alive briefly
                detach=True,
                mem_limit="512m",
                cpus=1.0,
                network_disabled=True, # Isolation
                # remove=True - can't use with detach if we want to copy files
            )
            
            # 2. Copy code to container
            # Docker API needs tar stream
            script_content = code.encode('utf-8')
            tar_stream = io.BytesIO()
            with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                tar_info = tarfile.TarInfo(name='script.py')
                tar_info.size = len(script_content)
                tar.addfile(tar_info, io.BytesIO(script_content))
            tar_stream.seek(0)
            
            container.put_archive('/app', tar_stream)
            
            # 3. Execute script with timeout
            import concurrent.futures
            
            def run_container_cmd():
                return container.exec_run(
                    cmd=f"python3 /app/script.py",
                    workdir="/app",
                    environment=env,
                )
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(run_container_cmd)
                try:
                    exit_code, output = future.result(timeout=timeout)
                    return output.decode('utf-8')
                except concurrent.futures.TimeoutError:
                    return f"Error: Execution timed out after {timeout} seconds."

        except Exception as e:
            return f"Docker Execution Error: {str(e)}"
        finally:
            if container:
                try:
                    container.kill()
                    container.remove()
                except:
                    pass

    def cleanup(self):
        pass
