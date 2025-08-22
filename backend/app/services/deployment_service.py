import docker
import json
import os
import asyncio
from typing import Dict, Any
import requests
from pathlib import Path

from app.models import Model, Deployment

class DeploymentService:
    def __init__(self):
        self.client = docker.from_env()
        self.base_port = 9000
        self.deployments = {}  # In-memory deployment tracking
        
    def deploy_model(self, deployment_id: int, model: Model, deployment_config) -> Dict[str, Any]:
        """Deploy a model as a containerized service"""
        
        port = self.base_port + deployment_id
        container_name = f"deployment-{deployment_id}"
        
        # Create deployment container based on model type
        if model.model_type in ["sklearn", "joblib"]:
            image = "python:3.10-slim"
            app_code = self._generate_sklearn_app(model)
        elif model.model_type in ["pytorch", "torch"]:
            image = "pytorch/pytorch:latest"
            app_code = self._generate_pytorch_app(model)
        elif model.model_type in ["tensorflow", "keras"]:
            image = "tensorflow/tensorflow:latest-gpu" if deployment_config.instance_type.startswith("gpu") else "tensorflow/tensorflow:latest"
            app_code = self._generate_tensorflow_app(model)
        else:
            raise Exception(f"Unsupported model type: {model.model_type}")
        
        # Create temporary directory with app code
        temp_dir = Path(f"/tmp/deployment-{deployment_id}")
        temp_dir.mkdir(exist_ok=True)
        
        # Write app code
        with open(temp_dir / "app.py", "w") as f:
            f.write(app_code)
        
        # Write requirements
        requirements = model.requirements or ["fastapi", "uvicorn", "numpy"]
        with open(temp_dir / "requirements.txt", "w") as f:
            f.write("\n".join(requirements))
        
        # Write Dockerfile
        dockerfile_content = self._generate_dockerfile(image, model.model_type)
        with open(temp_dir / "Dockerfile", "w") as f:
            f.write(dockerfile_content)
        
        try:
            # Build custom image
            image_tag = f"deployment-{deployment_id}:latest"
            self.client.images.build(
                path=str(temp_dir),
                tag=image_tag,
                rm=True
            )
            
            # Run container
            container = self.client.containers.run(
                image_tag,
                name=container_name,
                ports={8000: port},
                detach=True,
                restart_policy={"Name": "unless-stopped"},
                environment={
                    "MODEL_PATH": model.model_path,
                    "MODEL_TYPE": model.model_type
                }
            )
            
            # Store deployment info
            self.deployments[deployment_id] = {
                "container_id": container.id,
                "port": port,
                "status": "running"
            }
            
            # Wait for container to be ready
            self._wait_for_container_ready(f"http://localhost:{port}/health", timeout=60)
            
            return {
                "container_id": container.id,
                "endpoint_url": f"http://localhost:{port}",
                "status": "running"
            }
            
        except Exception as e:
            raise Exception(f"Failed to deploy model: {str(e)}")
        
        finally:
            # Clean up temp directory
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    async def predict(self, deployment_id: int, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make prediction using deployed model"""
        
        deployment_info = self.deployments.get(deployment_id)
        if not deployment_info:
            raise Exception("Deployment not found")
        
        port = deployment_info["port"]
        
        try:
            response = requests.post(
                f"http://localhost:{port}/predict",
                json=input_data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"Prediction request failed: {str(e)}")
    
    def scale_deployment(self, deployment_id: int, scale_config: Dict[str, Any]):
        """Scale deployment (placeholder for Kubernetes integration)"""
        # In a real implementation, this would interact with Kubernetes
        # to scale the deployment based on the configuration
        pass
    
    def stop_deployment(self, deployment_id: int):
        """Stop and remove deployment"""
        
        deployment_info = self.deployments.get(deployment_id)
        if deployment_info:
            try:
                container = self.client.containers.get(deployment_info["container_id"])
                container.stop()
                container.remove()
                del self.deployments[deployment_id]
            except Exception:
                pass
    
    def _generate_sklearn_app(self, model: Model) -> str:
        """Generate FastAPI app code for sklearn models"""
        return f'''
import pickle
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Model API - {model.name}")

# Load model
try:
    with open("/model/model.pkl", "rb") as f:
        model = pickle.load(f)
except Exception as e:
    print(f"Error loading model: {{e}}")
    model = None

class PredictionRequest(BaseModel):
    features: list

class PredictionResponse(BaseModel):
    prediction: list

@app.get("/health")
def health_check():
    return {{"status": "healthy", "model_loaded": model is not None}}

@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    try:
        features = np.array(request.features).reshape(1, -1)
        prediction = model.predict(features)
        return PredictionResponse(prediction=prediction.tolist())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction error: {{str(e)}}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
    
    def _generate_pytorch_app(self, model: Model) -> str:
        """Generate FastAPI app code for PyTorch models"""
        return f'''
import torch
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="PyTorch Model API - {model.name}")

# Load model
try:
    model = torch.load("/model/model.pt", map_location="cpu")
    model.eval()
except Exception as e:
    print(f"Error loading model: {{e}}")
    model = None

class PredictionRequest(BaseModel):
    features: list

class PredictionResponse(BaseModel):
    prediction: list

@app.get("/health")
def health_check():
    return {{"status": "healthy", "model_loaded": model is not None}}

@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    try:
        features = torch.tensor(request.features, dtype=torch.float32)
        with torch.no_grad():
            prediction = model(features)
        return PredictionResponse(prediction=prediction.tolist())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction error: {{str(e)}}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
    
    def _generate_tensorflow_app(self, model: Model) -> str:
        """Generate FastAPI app code for TensorFlow models"""
        return f'''
import tensorflow as tf
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="TensorFlow Model API - {model.name}")

# Load model
try:
    model = tf.keras.models.load_model("/model/model.h5")
except Exception as e:
    print(f"Error loading model: {{e}}")
    model = None

class PredictionRequest(BaseModel):
    features: list

class PredictionResponse(BaseModel):
    prediction: list

@app.get("/health")
def health_check():
    return {{"status": "healthy", "model_loaded": model is not None}}

@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    try:
        features = np.array(request.features).reshape(1, -1)
        prediction = model.predict(features)
        return PredictionResponse(prediction=prediction.tolist())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction error: {{str(e)}}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
    
    def _generate_dockerfile(self, base_image: str, model_type: str) -> str:
        """Generate Dockerfile for deployment"""
        return f'''
FROM {base_image}

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Model will be mounted as volume
VOLUME ["/model"]

EXPOSE 8000

CMD ["python", "app.py"]
'''
    
    def _wait_for_container_ready(self, health_url: str, timeout: int = 60):
        """Wait for container to be ready"""
        import time
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(health_url, timeout=5)
                if response.status_code == 200:
                    return True
            except:
                pass
            time.sleep(2)
        
        raise Exception("Container failed to become ready within timeout")