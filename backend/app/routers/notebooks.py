from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import uuid
import docker
import os

from app.database import get_db
from app.models import User, Notebook, UsageRecord
from app.schemas import NotebookCreate, NotebookResponse
from app.routers.auth import get_current_user
from app.services.container_service import ContainerService

router = APIRouter()
container_service = ContainerService()

@router.get("/", response_model=List[NotebookResponse])
def get_notebooks(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notebooks = db.query(Notebook).filter(Notebook.owner_id == current_user.id).all()
    return notebooks

@router.post("/", response_model=NotebookResponse)
def create_notebook(
    notebook: NotebookCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Create notebook record
    db_notebook = Notebook(
        name=notebook.name,
        description=notebook.description,
        owner_id=current_user.id,
        gpu_type=notebook.gpu_type,
        cpu_cores=notebook.cpu_cores,
        memory_gb=notebook.memory_gb,
        storage_gb=notebook.storage_gb,
        status="creating"
    )
    db.add(db_notebook)
    db.commit()
    db.refresh(db_notebook)
    
    try:
        # Start container
        container_info = container_service.create_notebook_container(
            notebook_id=db_notebook.id,
            user_id=current_user.id,
            gpu_type=notebook.gpu_type,
            cpu_cores=notebook.cpu_cores,
            memory_gb=notebook.memory_gb
        )
        
        # Update notebook with container info
        db_notebook.container_id = container_info["container_id"]
        db_notebook.jupyter_url = container_info["jupyter_url"]
        db_notebook.status = "running"
        db.commit()
        
        # Create usage record
        usage_record = UsageRecord(
            user_id=current_user.id,
            notebook_id=db_notebook.id,
            resource_type="notebook_runtime",
            start_time=db_notebook.created_at,
            metadata={
                "gpu_type": notebook.gpu_type,
                "cpu_cores": notebook.cpu_cores,
                "memory_gb": notebook.memory_gb
            }
        )
        db.add(usage_record)
        db.commit()
        
    except Exception as e:
        db_notebook.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to create notebook: {str(e)}")
    
    return db_notebook

@router.get("/{notebook_id}", response_model=NotebookResponse)
def get_notebook(
    notebook_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notebook = db.query(Notebook).filter(
        Notebook.id == notebook_id,
        Notebook.owner_id == current_user.id
    ).first()
    
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")
    
    return notebook

@router.post("/{notebook_id}/start")
def start_notebook(
    notebook_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notebook = db.query(Notebook).filter(
        Notebook.id == notebook_id,
        Notebook.owner_id == current_user.id
    ).first()
    
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")
    
    if notebook.status == "running":
        return {"message": "Notebook is already running", "jupyter_url": notebook.jupyter_url}
    
    try:
        # Start container
        container_info = container_service.start_notebook_container(notebook.container_id)
        
        notebook.jupyter_url = container_info["jupyter_url"]
        notebook.status = "running"
        db.commit()
        
        # Create new usage record
        usage_record = UsageRecord(
            user_id=current_user.id,
            notebook_id=notebook.id,
            resource_type="notebook_runtime",
            start_time=datetime.utcnow()
        )
        db.add(usage_record)
        db.commit()
        
        return {"message": "Notebook started", "jupyter_url": notebook.jupyter_url}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start notebook: {str(e)}")

@router.post("/{notebook_id}/stop")
def stop_notebook(
    notebook_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notebook = db.query(Notebook).filter(
        Notebook.id == notebook_id,
        Notebook.owner_id == current_user.id
    ).first()
    
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")
    
    try:
        # Stop container
        container_service.stop_notebook_container(notebook.container_id)
        
        notebook.status = "stopped"
        notebook.jupyter_url = None
        db.commit()
        
        # Update usage record
        usage_record = db.query(UsageRecord).filter(
            UsageRecord.notebook_id == notebook.id,
            UsageRecord.end_time == None
        ).order_by(UsageRecord.start_time.desc()).first()
        
        if usage_record:
            from datetime import datetime
            usage_record.end_time = datetime.utcnow()
            usage_record.duration_minutes = (usage_record.end_time - usage_record.start_time).total_seconds() / 60
            # Calculate cost based on GPU type and duration
            usage_record.cost = container_service.calculate_cost(notebook.gpu_type, usage_record.duration_minutes)
            db.commit()
        
        return {"message": "Notebook stopped"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop notebook: {str(e)}")

@router.delete("/{notebook_id}")
def delete_notebook(
    notebook_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notebook = db.query(Notebook).filter(
        Notebook.id == notebook_id,
        Notebook.owner_id == current_user.id
    ).first()
    
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")
    
    try:
        # Stop and remove container
        if notebook.container_id:
            container_service.delete_notebook_container(notebook.container_id)
        
        # Delete notebook record
        db.delete(notebook)
        db.commit()
        
        return {"message": "Notebook deleted"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete notebook: {str(e)}")