from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    notebooks = relationship("Notebook", back_populates="owner")
    models = relationship("Model", back_populates="owner")
    deployments = relationship("Deployment", back_populates="owner")
    usage_records = relationship("UsageRecord", back_populates="user")

class Notebook(Base):
    __tablename__ = "notebooks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="stopped")  # running, stopped, starting, stopping
    gpu_type = Column(String)  # tesla-v100, tesla-t4, rtx-4090, etc.
    cpu_cores = Column(Integer, default=2)
    memory_gb = Column(Integer, default=8)
    storage_gb = Column(Integer, default=50)
    jupyter_url = Column(String)
    container_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="notebooks")
    usage_records = relationship("UsageRecord", back_populates="notebook")

class Model(Base):
    __tablename__ = "models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    notebook_id = Column(Integer, ForeignKey("notebooks.id"))
    model_type = Column(String)  # sklearn, pytorch, tensorflow, etc.
    framework_version = Column(String)
    model_path = Column(String)  # S3 or local storage path
    requirements = Column(JSON)  # List of Python packages
    status = Column(String, default="training")  # training, ready, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="models")
    deployments = relationship("Deployment", back_populates="model")

class Deployment(Base):
    __tablename__ = "deployments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    model_id = Column(Integer, ForeignKey("models.id"))
    owner_id = Column(Integer, ForeignKey("users.id"))
    api_endpoint = Column(String, unique=True)
    api_key = Column(String, unique=True)
    status = Column(String, default="deploying")  # deploying, running, stopped, failed
    instance_type = Column(String)  # cpu, gpu-t4, gpu-v100, etc.
    auto_scaling = Column(Boolean, default=False)
    min_instances = Column(Integer, default=1)
    max_instances = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="deployments")
    model = relationship("Model", back_populates="deployments")
    api_calls = relationship("ApiCall", back_populates="deployment")

class UsageRecord(Base):
    __tablename__ = "usage_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    notebook_id = Column(Integer, ForeignKey("notebooks.id"), nullable=True)
    deployment_id = Column(Integer, ForeignKey("deployments.id"), nullable=True)
    resource_type = Column(String)  # notebook_runtime, api_call, storage
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration_minutes = Column(Float)
    cost = Column(Float)
    metadata = Column(JSON)  # Additional usage details
    
    # Relationships
    user = relationship("User", back_populates="usage_records")
    notebook = relationship("Notebook", back_populates="usage_records")

class ApiCall(Base):
    __tablename__ = "api_calls"
    
    id = Column(Integer, primary_key=True, index=True)
    deployment_id = Column(Integer, ForeignKey("deployments.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    response_time_ms = Column(Float)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    success = Column(Boolean, default=True)
    error_message = Column(String, nullable=True)
    
    # Relationships
    deployment = relationship("Deployment", back_populates="api_calls")