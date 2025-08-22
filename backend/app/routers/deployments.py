from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uuid
from datetime import datetime

from app.database import get_db
from app.models import User, Deployment, Model, ApiCall
from app.schemas import DeploymentCreate, DeploymentResponse
from app.routers.auth import get_current_user
from app.services.deployment_service import DeploymentService

router = APIRouter()
deployment_service = DeploymentService()

@router.get("/", response_model=List[DeploymentResponse])
def get_deployments(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    deployments = db.query(Deployment).filter(Deployment.owner_id == current_user.id).all()
    return deployments

@router.post("/", response_model=DeploymentResponse)
def create_deployment(
    deployment: DeploymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify model belongs to user
    model = db.query(Model).filter(
        Model.id == deployment.model_id,
        Model.owner_id == current_user.id,
        Model.status == "ready"
    ).first()
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found or not ready")
    
    # Generate API key and endpoint
    api_key = f"ml_{uuid.uuid4().hex}"
    api_endpoint = f"/api/predict/{uuid.uuid4().hex}"
    
    # Create deployment record
    db_deployment = Deployment(
        name=deployment.name,
        model_id=deployment.model_id,
        owner_id=current_user.id,
        api_endpoint=api_endpoint,
        api_key=api_key,
        status="deploying",
        instance_type=deployment.instance_type,
        auto_scaling=deployment.auto_scaling,
        min_instances=deployment.min_instances,
        max_instances=deployment.max_instances
    )
    db.add(db_deployment)
    db.commit()
    db.refresh(db_deployment)
    
    try:
        # Deploy model
        deployment_info = deployment_service.deploy_model(
            deployment_id=db_deployment.id,
            model=model,
            deployment_config=deployment
        )
        
        # Update deployment status
        db_deployment.status = "running"
        db.commit()
        
        return db_deployment
        
    except Exception as e:
        db_deployment.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to deploy model: {str(e)}")

@router.get("/{deployment_id}", response_model=DeploymentResponse)
def get_deployment(
    deployment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    deployment = db.query(Deployment).filter(
        Deployment.id == deployment_id,
        Deployment.owner_id == current_user.id
    ).first()
    
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    return deployment

@router.post("/{deployment_id}/predict")
async def predict(
    deployment_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    # Get deployment
    deployment = db.query(Deployment).filter(
        Deployment.id == deployment_id,
        Deployment.status == "running"
    ).first()
    
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found or not running")
    
    # Verify API key
    api_key = request.headers.get("X-API-Key")
    if api_key != deployment.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        start_time = datetime.utcnow()
        
        # Get request body
        body = await request.json()
        
        # Make prediction
        result = await deployment_service.predict(deployment.id, body)
        
        end_time = datetime.utcnow()
        response_time = (end_time - start_time).total_seconds() * 1000
        
        # Log API call
        api_call = ApiCall(
            deployment_id=deployment.id,
            response_time_ms=response_time,
            success=True
        )
        db.add(api_call)
        db.commit()
        
        return result
        
    except Exception as e:
        # Log failed API call
        api_call = ApiCall(
            deployment_id=deployment.id,
            success=False,
            error_message=str(e)
        )
        db.add(api_call)
        db.commit()
        
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.post("/{deployment_id}/scale")
def scale_deployment(
    deployment_id: int,
    scale_config: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    deployment = db.query(Deployment).filter(
        Deployment.id == deployment_id,
        Deployment.owner_id == current_user.id
    ).first()
    
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    try:
        deployment_service.scale_deployment(deployment_id, scale_config)
        
        # Update deployment config
        if "min_instances" in scale_config:
            deployment.min_instances = scale_config["min_instances"]
        if "max_instances" in scale_config:
            deployment.max_instances = scale_config["max_instances"]
        
        db.commit()
        
        return {"message": "Deployment scaled successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to scale deployment: {str(e)}")

@router.delete("/{deployment_id}")
def delete_deployment(
    deployment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    deployment = db.query(Deployment).filter(
        Deployment.id == deployment_id,
        Deployment.owner_id == current_user.id
    ).first()
    
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    try:
        # Stop deployment
        deployment_service.stop_deployment(deployment_id)
        
        # Delete deployment record
        db.delete(deployment)
        db.commit()
        
        return {"message": "Deployment deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete deployment: {str(e)}")