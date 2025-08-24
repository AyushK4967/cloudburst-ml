import mlflow
import mlflow.tracking
from mlflow.tracking import MlflowClient
from mlflow.store.artifact.s3_artifact_repo import S3ArtifactRepository
import os
import logging
from typing import Dict, List, Optional, Any
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class MLflowIntegration:
    def __init__(self):
        self.tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
        self.s3_endpoint = os.getenv("MLFLOW_S3_ENDPOINT_URL", "http://minio:9000")
        self.s3_access_key = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
        self.s3_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin123")
        
        # Set MLflow tracking URI
        mlflow.set_tracking_uri(self.tracking_uri)
        self.client = MlflowClient(tracking_uri=self.tracking_uri)
        
        # Configure S3 client for MinIO
        self.s3_client = boto3.client(
            's3',
            endpoint_url=self.s3_endpoint,
            aws_access_key_id=self.s3_access_key,
            aws_secret_access_key=self.s3_secret_key,
            region_name='us-east-1'
        )
        
        # Ensure MLflow bucket exists
        self._ensure_mlflow_bucket()
        
        logger.info(f"MLflow client initialized with tracking URI: {self.tracking_uri}")
    
    def _ensure_mlflow_bucket(self):
        """Ensure MLflow artifacts bucket exists"""
        bucket_name = "ml-models"
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                try:
                    self.s3_client.create_bucket(Bucket=bucket_name)
                    logger.info(f"Created MLflow bucket: {bucket_name}")
                except ClientError as create_error:
                    logger.error(f"Failed to create MLflow bucket: {create_error}")
    
    def create_experiment(self, name: str, tags: Optional[Dict[str, str]] = None) -> str:
        """Create a new MLflow experiment"""
        try:
            experiment_id = self.client.create_experiment(
                name=name,
                tags=tags or {}
            )
            logger.info(f"Created experiment: {name} (ID: {experiment_id})")
            return experiment_id
        except Exception as e:
            logger.error(f"Failed to create experiment {name}: {e}")
            raise
    
    def start_run(self, experiment_name: str, run_name: Optional[str] = None, tags: Optional[Dict[str, str]] = None) -> str:
        """Start a new MLflow run"""
        try:
            # Get or create experiment
            try:
                experiment = self.client.get_experiment_by_name(experiment_name)
                experiment_id = experiment.experiment_id
            except:
                experiment_id = self.create_experiment(experiment_name)
            
            # Start run
            run = self.client.create_run(
                experiment_id=experiment_id,
                tags=tags or {},
                run_name=run_name
            )
            
            logger.info(f"Started run: {run.info.run_id} in experiment: {experiment_name}")
            return run.info.run_id
            
        except Exception as e:
            logger.error(f"Failed to start run: {e}")
            raise
    
    def log_param(self, run_id: str, key: str, value: Any):
        """Log a parameter to MLflow run"""
        try:
            self.client.log_param(run_id, key, value)
        except Exception as e:
            logger.error(f"Failed to log param {key}: {e}")
    
    def log_metric(self, run_id: str, key: str, value: float, step: Optional[int] = None):
        """Log a metric to MLflow run"""
        try:
            self.client.log_metric(run_id, key, value, step=step)
        except Exception as e:
            logger.error(f"Failed to log metric {key}: {e}")
    
    def log_artifact(self, run_id: str, local_path: str, artifact_path: Optional[str] = None):
        """Log an artifact to MLflow run"""
        try:
            self.client.log_artifact(run_id, local_path, artifact_path)
        except Exception as e:
            logger.error(f"Failed to log artifact: {e}")
    
    def log_model(self, run_id: str, model, artifact_path: str, registered_model_name: Optional[str] = None):
        """Log a model to MLflow"""
        try:
            # Set the active run
            with mlflow.start_run(run_id=run_id):
                model_info = mlflow.sklearn.log_model(
                    sk_model=model,
                    artifact_path=artifact_path,
                    registered_model_name=registered_model_name
                )
            
            logger.info(f"Logged model to run {run_id}: {model_info.model_uri}")
            return model_info
            
        except Exception as e:
            logger.error(f"Failed to log model: {e}")
            raise
    
    def register_model(self, model_uri: str, model_name: str, tags: Optional[Dict[str, str]] = None) -> str:
        """Register a model in MLflow Model Registry"""
        try:
            model_version = self.client.create_model_version(
                name=model_name,
                source=model_uri,
                tags=tags or {}
            )
            
            logger.info(f"Registered model {model_name} version {model_version.version}")
            return model_version.version
            
        except Exception as e:
            logger.error(f"Failed to register model: {e}")
            raise
    
    def get_model_version(self, model_name: str, version: str) -> Dict:
        """Get model version details"""
        try:
            model_version = self.client.get_model_version(model_name, version)
            return {
                "name": model_version.name,
                "version": model_version.version,
                "source": model_version.source,
                "status": model_version.status,
                "tags": model_version.tags,
                "creation_timestamp": model_version.creation_timestamp
            }
        except Exception as e:
            logger.error(f"Failed to get model version: {e}")
            raise
    
    def list_registered_models(self) -> List[Dict]:
        """List all registered models"""
        try:
            models = self.client.search_registered_models()
            return [
                {
                    "name": model.name,
                    "description": model.description,
                    "tags": model.tags,
                    "latest_versions": [
                        {
                            "version": version.version,
                            "stage": version.current_stage,
                            "status": version.status
                        }
                        for version in model.latest_versions
                    ]
                }
                for model in models
            ]
        except Exception as e:
            logger.error(f"Failed to list registered models: {e}")
            return []
    
    def transition_model_stage(self, model_name: str, version: str, stage: str):
        """Transition model version stage"""
        try:
            self.client.transition_model_version_stage(
                name=model_name,
                version=version,
                stage=stage
            )
            logger.info(f"Transitioned {model_name} v{version} to {stage}")
        except Exception as e:
            logger.error(f"Failed to transition model stage: {e}")
            raise
    
    def search_runs(self, experiment_ids: List[str], filter_string: str = "", max_results: int = 100) -> List[Dict]:
        """Search runs in experiments"""
        try:
            runs = self.client.search_runs(
                experiment_ids=experiment_ids,
                filter_string=filter_string,
                max_results=max_results
            )
            
            return [
                {
                    "run_id": run.info.run_id,
                    "experiment_id": run.info.experiment_id,
                    "status": run.info.status,
                    "start_time": run.info.start_time,
                    "end_time": run.info.end_time,
                    "params": run.data.params,
                    "metrics": run.data.metrics,
                    "tags": run.data.tags
                }
                for run in runs
            ]
        except Exception as e:
            logger.error(f"Failed to search runs: {e}")
            return []
    
    def get_experiment_by_name(self, name: str) -> Optional[Dict]:
        """Get experiment by name"""
        try:
            experiment = self.client.get_experiment_by_name(name)
            if experiment:
                return {
                    "experiment_id": experiment.experiment_id,
                    "name": experiment.name,
                    "lifecycle_stage": experiment.lifecycle_stage,
                    "tags": experiment.tags
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get experiment {name}: {e}")
            return None
    
    def delete_experiment(self, experiment_id: str):
        """Delete an experiment"""
        try:
            self.client.delete_experiment(experiment_id)
            logger.info(f"Deleted experiment: {experiment_id}")
        except Exception as e:
            logger.error(f"Failed to delete experiment: {e}")
            raise
    
    def get_run_details(self, run_id: str) -> Optional[Dict]:
        """Get detailed information about a specific run"""
        try:
            run = self.client.get_run(run_id)
            return {
                "run_id": run.info.run_id,
                "experiment_id": run.info.experiment_id,
                "status": run.info.status,
                "start_time": run.info.start_time,
                "end_time": run.info.end_time,
                "params": run.data.params,
                "metrics": run.data.metrics,
                "tags": run.data.tags,
                "artifact_uri": run.info.artifact_uri
            }
        except Exception as e:
            logger.error(f"Failed to get run details: {e}")
            return None

# Global MLflow client instance
mlflow_client = MLflowIntegration()