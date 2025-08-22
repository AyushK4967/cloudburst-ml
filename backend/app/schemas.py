from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# Notebook schemas
class NotebookBase(BaseModel):
    name: str
    description: Optional[str] = None
    gpu_type: Optional[str] = None
    cpu_cores: int = 2
    memory_gb: int = 8
    storage_gb: int = 50

class NotebookCreate(NotebookBase):
    pass

class NotebookResponse(NotebookBase):
    id: int
    owner_id: int
    status: str
    jupyter_url: Optional[str]
    created_at: datetime
    last_accessed: datetime
    
    class Config:
        from_attributes = True

# Model schemas
class ModelBase(BaseModel):
    name: str
    description: Optional[str] = None
    model_type: str
    framework_version: Optional[str] = None

class ModelCreate(ModelBase):
    notebook_id: int
    requirements: Optional[List[str]] = []

class ModelResponse(ModelBase):
    id: int
    owner_id: int
    notebook_id: int
    status: str
    model_path: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Deployment schemas
class DeploymentBase(BaseModel):
    name: str
    instance_type: str = "cpu"
    auto_scaling: bool = False
    min_instances: int = 1
    max_instances: int = 5

class DeploymentCreate(DeploymentBase):
    model_id: int

class DeploymentResponse(DeploymentBase):
    id: int
    model_id: int
    owner_id: int
    api_endpoint: str
    api_key: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Usage schemas
class UsageRecord(BaseModel):
    resource_type: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_minutes: Optional[float]
    cost: Optional[float]
    
    class Config:
        from_attributes = True

class BillingResponse(BaseModel):
    current_month_cost: float
    total_cost: float
    usage_records: List[UsageRecord]