from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from app.database import engine, get_db
from app.routers import auth, notebooks, models, billing, deployments
from app.models import Base

load_dotenv()

# Create tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting ML Cloud Platform...")
    yield
    # Shutdown
    print("Shutting down...")

app = FastAPI(
    title="ML Cloud Platform API",
    description="Cloud platform for ML models with Jupyter notebooks and GPU support",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(notebooks.router, prefix="/api/notebooks", tags=["notebooks"])
app.include_router(models.router, prefix="/api/models", tags=["models"])
app.include_router(deployments.router, prefix="/api/deployments", tags=["deployments"])
app.include_router(billing.router, prefix="/api/billing", tags=["billing"])

@app.get("/")
async def root():
    return {"message": "ML Cloud Platform API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}