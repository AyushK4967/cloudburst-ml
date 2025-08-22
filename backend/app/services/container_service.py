import docker
import uuid
import os
from typing import Dict, Any

class ContainerService:
    def __init__(self):
        self.client = docker.from_env()
        self.base_port = 8888
        
    def create_notebook_container(self, notebook_id: int, user_id: int, gpu_type: str, cpu_cores: int, memory_gb: int) -> Dict[str, Any]:
        """Create and start a Jupyter notebook container"""
        
        # Generate unique port and token
        port = self.base_port + notebook_id
        token = str(uuid.uuid4())
        container_name = f"notebook-{notebook_id}-{user_id}"
        
        # Docker image selection based on GPU type
        if gpu_type:
            image = "jupyter/tensorflow-notebook:python-3.10"  # GPU-enabled image
            runtime = "nvidia"
        else:
            image = "jupyter/datascience-notebook:python-3.10"
            runtime = None
        
        # Container configuration
        container_config = {
            "image": image,
            "name": container_name,
            "ports": {f"{self.base_port}/tcp": port},
            "environment": [
                f"JUPYTER_TOKEN={token}",
                "JUPYTER_ENABLE_LAB=yes",
                f"NB_USER=jovyan",
                f"CHOWN_HOME=yes",
                f"CHOWN_HOME_OPTS=-R"
            ],
            "volumes": {
                f"notebook-data-{notebook_id}": {"bind": "/home/jovyan/work", "mode": "rw"}
            },
            "mem_limit": f"{memory_gb}g",
            "cpu_count": cpu_cores,
            "detach": True,
            "restart_policy": {"Name": "unless-stopped"}
        }
        
        # Add GPU support if needed
        if gpu_type and runtime:
            container_config["runtime"] = runtime
            container_config["device_requests"] = [
                docker.types.DeviceRequest(count=-1, capabilities=[["gpu"]])
            ]
        
        try:
            # Pull image if not exists
            self.client.images.pull(image)
            
            # Create and start container
            container = self.client.containers.run(**container_config)
            
            # Wait for container to be ready
            container.reload()
            
            jupyter_url = f"http://localhost:{port}/?token={token}"
            
            return {
                "container_id": container.id,
                "jupyter_url": jupyter_url,
                "port": port,
                "token": token,
                "status": "running"
            }
            
        except Exception as e:
            raise Exception(f"Failed to create container: {str(e)}")
    
    def start_notebook_container(self, container_id: str) -> Dict[str, Any]:
        """Start an existing notebook container"""
        try:
            container = self.client.containers.get(container_id)
            container.start()
            
            # Get container info
            container.reload()
            port_info = container.attrs['NetworkSettings']['Ports']
            port = list(port_info.keys())[0].split('/')[0] if port_info else self.base_port
            
            # Extract token from environment
            env_vars = container.attrs['Config']['Env']
            token = None
            for env in env_vars:
                if env.startswith('JUPYTER_TOKEN='):
                    token = env.split('=')[1]
                    break
            
            jupyter_url = f"http://localhost:{port}/?token={token}"
            
            return {
                "jupyter_url": jupyter_url,
                "status": "running"
            }
            
        except Exception as e:
            raise Exception(f"Failed to start container: {str(e)}")
    
    def stop_notebook_container(self, container_id: str):
        """Stop a notebook container"""
        try:
            container = self.client.containers.get(container_id)
            container.stop()
        except Exception as e:
            raise Exception(f"Failed to stop container: {str(e)}")
    
    def delete_notebook_container(self, container_id: str):
        """Delete a notebook container"""
        try:
            container = self.client.containers.get(container_id)
            container.stop()
            container.remove()
        except Exception as e:
            raise Exception(f"Failed to delete container: {str(e)}")
    
    def calculate_cost(self, gpu_type: str, duration_minutes: float) -> float:
        """Calculate cost based on GPU type and duration"""
        
        # Pricing per minute (example rates)
        pricing = {
            "tesla-v100": 0.05,    # $3/hour
            "tesla-t4": 0.02,      # $1.2/hour
            "rtx-4090": 0.03,      # $1.8/hour
            "cpu": 0.005,          # $0.3/hour
            None: 0.005            # CPU only
        }
        
        rate = pricing.get(gpu_type, pricing["cpu"])
        return rate * duration_minutes
    
    def get_container_status(self, container_id: str) -> str:
        """Get container status"""
        try:
            container = self.client.containers.get(container_id)
            return container.status
        except:
            return "not_found"
    
    def get_container_logs(self, container_id: str, tail: int = 100) -> str:
        """Get container logs"""
        try:
            container = self.client.containers.get(container_id)
            logs = container.logs(tail=tail, timestamps=True)
            return logs.decode('utf-8')
        except Exception as e:
            return f"Error getting logs: {str(e)}"