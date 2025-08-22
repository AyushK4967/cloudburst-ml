from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import shutil
import os
from datetime import datetime

from app.database import get_db
from app.models import User, Model, Notebook
from app.schemas import ModelCreate, ModelResponse
from app.routers.auth import get_current_user
from app.services.model_service import ModelService

router = APIRouter()
model_service = ModelService()

@router.get("/", response_model=List[ModelResponse])
def get_models(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    models = db.query(Model).filter(Model.owner_id == current_user.id).all()
    return models

@router.post("/", response_model=ModelResponse)
def create_model(
    model: ModelCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify notebook belongs to user
    notebook = db.query(Notebook).filter(
        Notebook.id == model.notebook_id,
        Notebook.owner_id == current_user.id
    ).first()
    
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")
    
    # Create model record
    db_model = Model(
        name=model.name,
        description=model.description,
        owner_id=current_user.id,
        notebook_id=model.notebook_id,
        model_type=model.model_type,
        framework_version=model.framework_version,
        requirements=model.requirements,
        status="training"
    )
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    
    return db_model

@router.post("/{model_id}/upload")
def upload_model_file(
    model_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify model belongs to user
    model = db.query(Model).filter(
        Model.id == model_id,
        Model.owner_id == current_user.id
    ).first()
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    try:
        # Save file to storage
        file_path = model_service.save_model_file(model_id, file)
        
        # Update model record
        model.model_path = file_path
        model.status = "ready"
        db.commit()
        
        return {"message": "Model file uploaded successfully", "path": file_path}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload model: {str(e)}")

@router.get("/{model_id}", response_model=ModelResponse)
def get_model(
    model_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    model = db.query(Model).filter(
        Model.id == model_id,
        Model.owner_id == current_user.id
    ).first()
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return model

@router.delete("/{model_id}")
def delete_model(
    model_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    model = db.query(Model).filter(
        Model.id == model_id,
        Model.owner_id == current_user.id
    ).first()
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    try:
        # Delete model file
        if model.model_path:
            model_service.delete_model_file(model.model_path)
        
        # Delete model record
        db.delete(model)
        db.commit()
        
        return {"message": "Model deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete model: {str(e)}")