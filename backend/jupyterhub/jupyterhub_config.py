# JupyterHub Configuration for ML Platform
import os
from dockerspawner import DockerSpawner
from oauthenticator.generic import GenericOAuthenticator

# Basic JupyterHub configuration
c.JupyterHub.spawner_class = DockerSpawner
c.JupyterHub.hub_ip = '0.0.0.0'
c.JupyterHub.hub_port = 8080
c.JupyterHub.port = 8000

# Database configuration
c.JupyterHub.db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:password@db:5432/mlplatform')

# Docker spawner configuration
c.DockerSpawner.image = 'jupyter/tensorflow-notebook:latest'
c.DockerSpawner.network_name = 'backend_default'
c.DockerSpawner.remove = True
c.DockerSpawner.debug = True

# GPU support
c.DockerSpawner.extra_host_config = {
    'runtime': 'nvidia',
    'device_requests': [
        {
            'driver': 'nvidia',
            'count': 1,
            'capabilities': [['gpu']],
        }
    ],
}

# Resource limits
c.DockerSpawner.mem_limit = '8G'
c.DockerSpawner.cpu_limit = 2.0

# Volume mounts
c.DockerSpawner.volumes = {
    'jupyterhub-user-{username}': '/home/jovyan/work'
}

# Custom authenticator integration with our FastAPI backend
class MLPlatformAuthenticator(GenericOAuthenticator):
    login_service = "ML Platform"
    
    async def pre_spawn_start(self, user, spawner):
        """Called before the spawner starts"""
        auth_state = await user.get_auth_state()
        if not auth_state:
            return
        
        # Set environment variables for the notebook
        spawner.environment.update({
            'MLFLOW_TRACKING_URI': 'http://mlflow:5000',
            'MLPLATFORM_API_URL': 'http://backend:8000',
            'USER_ID': str(auth_state.get('user_id', '')),
        })

c.JupyterHub.authenticator_class = MLPlatformAuthenticator
c.MLPlatformAuthenticator.oauth_callback_url = 'http://localhost:8000/hub/oauth-callback'
c.MLPlatformAuthenticator.client_id = os.getenv('OAUTH_CLIENT_ID', 'jupyterhub')
c.MLPlatformAuthenticator.client_secret = os.getenv('OAUTH_CLIENT_SECRET', 'secret')

# Admin configuration
c.Authenticator.admin_users = {'admin'}
c.JupyterHub.admin_access = True

# Logging
c.JupyterHub.log_level = 'DEBUG'
c.Spawner.log_level = 'DEBUG'