from celery import Celery
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import docker

from app.database import SessionLocal
from app.models import Notebook, UsageRecord
from app.services.container_service import ContainerService
from app.celery_app import celery_app

container_service = ContainerService()

@celery_app.task
def cleanup_stopped_notebooks():
    """Clean up notebooks that have been stopped for more than 24 hours"""
    
    db = SessionLocal()
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        # Find notebooks stopped for more than 24 hours
        old_notebooks = db.query(Notebook).filter(
            Notebook.status == "stopped",
            Notebook.last_accessed < cutoff_time
        ).all()
        
        for notebook in old_notebooks:
            try:
                # Delete container and data
                if notebook.container_id:
                    container_service.delete_notebook_container(notebook.container_id)
                
                # Update notebook status
                notebook.status = "deleted"
                notebook.container_id = None
                notebook.jupyter_url = None
                
                db.commit()
                print(f"Cleaned up notebook {notebook.id}")
                
            except Exception as e:
                print(f"Error cleaning up notebook {notebook.id}: {e}")
                
    finally:
        db.close()

@celery_app.task
def calculate_usage_costs():
    """Calculate costs for running notebooks and update usage records"""
    
    db = SessionLocal()
    try:
        # Find running notebooks with incomplete usage records
        running_notebooks = db.query(Notebook).filter(
            Notebook.status == "running"
        ).all()
        
        for notebook in running_notebooks:
            # Find the latest usage record for this notebook
            usage_record = db.query(UsageRecord).filter(
                UsageRecord.notebook_id == notebook.id,
                UsageRecord.end_time == None
            ).order_by(UsageRecord.start_time.desc()).first()
            
            if usage_record:
                # Update duration and cost
                now = datetime.utcnow()
                usage_record.duration_minutes = (now - usage_record.start_time).total_seconds() / 60
                usage_record.cost = container_service.calculate_cost(
                    notebook.gpu_type, 
                    usage_record.duration_minutes
                )
                
                db.commit()
        
    except Exception as e:
        print(f"Error calculating usage costs: {e}")
    
    finally:
        db.close()

@celery_app.task
def deploy_model_async(deployment_id: int, model_id: int):
    """Deploy model asynchronously"""
    
    from app.services.deployment_service import DeploymentService
    from app.models import Deployment, Model
    
    db = SessionLocal()
    deployment_service = DeploymentService()
    
    try:
        deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
        model = db.query(Model).filter(Model.id == model_id).first()
        
        if not deployment or not model:
            return
        
        # Deploy the model
        deployment_info = deployment_service.deploy_model(
            deployment_id=deployment.id,
            model=model,
            deployment_config=deployment
        )
        
        # Update deployment status
        deployment.status = "running"
        db.commit()
        
        return {"status": "success", "deployment_info": deployment_info}
        
    except Exception as e:
        # Update deployment status to failed
        deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
        if deployment:
            deployment.status = "failed"
            db.commit()
        
        return {"status": "failed", "error": str(e)}
    
    finally:
        db.close()

@celery_app.task
def process_model_training(model_id: int, training_config: dict):
    """Process model training in background"""
    
    from app.models import Model
    
    db = SessionLocal()
    
    try:
        model = db.query(Model).filter(Model.id == model_id).first()
        if not model:
            return
        
        model.status = "training"
        db.commit()
        
        # Here you would implement the actual training logic
        # This could involve starting a training container, submitting to a job queue, etc.
        
        # Simulate training completion
        model.status = "ready"
        db.commit()
        
        return {"status": "success", "model_id": model_id}
        
    except Exception as e:
        model = db.query(Model).filter(Model.id == model_id).first()
        if model:
            model.status = "failed"
            db.commit()
        
        return {"status": "failed", "error": str(e)}
    
    finally:
        db.close()