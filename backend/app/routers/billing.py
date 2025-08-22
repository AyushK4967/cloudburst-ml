from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, func
from sqlalchemy import and_
from typing import List, Dict, Any
from datetime import datetime, timedelta
import stripe
import os

from app.database import get_db
from app.models import User, UsageRecord, ApiCall, Deployment
from app.schemas import BillingResponse
from app.routers.auth import get_current_user

router = APIRouter()

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_...")

@router.get("/usage", response_model=BillingResponse)
def get_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get current month usage
    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)
    
    usage_records = db.query(UsageRecord).filter(
        and_(
            UsageRecord.user_id == current_user.id,
            UsageRecord.start_time >= month_start
        )
    ).all()
    
    # Calculate current month cost
    current_month_cost = sum(record.cost or 0 for record in usage_records)
    
    # Calculate total cost
    total_usage = db.query(UsageRecord).filter(
        UsageRecord.user_id == current_user.id
    ).all()
    total_cost = sum(record.cost or 0 for record in total_usage)
    
    return BillingResponse(
        current_month_cost=current_month_cost,
        total_cost=total_cost,
        usage_records=[
            {
                "resource_type": record.resource_type,
                "start_time": record.start_time,
                "end_time": record.end_time,
                "duration_minutes": record.duration_minutes,
                "cost": record.cost
            }
            for record in usage_records
        ]
    )

@router.get("/stats")
def get_billing_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get usage by resource type
    usage_by_type = db.query(
        UsageRecord.resource_type,
        func.sum(UsageRecord.cost).label("total_cost"),
        func.sum(UsageRecord.duration_minutes).label("total_duration")
    ).filter(
        UsageRecord.user_id == current_user.id
    ).group_by(UsageRecord.resource_type).all()
    
    # Get API call stats for deployments
    api_stats = db.query(
        func.count(ApiCall.id).label("total_calls"),
        func.avg(ApiCall.response_time_ms).label("avg_response_time"),
        func.sum(func.case([(ApiCall.success == True, 1)], else_=0)).label("successful_calls")
    ).join(Deployment).filter(
        Deployment.owner_id == current_user.id
    ).first()
    
    return {
        "usage_by_type": [
            {
                "resource_type": usage.resource_type,
                "total_cost": float(usage.total_cost or 0),
                "total_duration": float(usage.total_duration or 0)
            }
            for usage in usage_by_type
        ],
        "api_stats": {
            "total_calls": api_stats.total_calls or 0,
            "avg_response_time_ms": float(api_stats.avg_response_time or 0),
            "successful_calls": api_stats.successful_calls or 0,
            "success_rate": (api_stats.successful_calls or 0) / max(api_stats.total_calls or 1, 1) * 100
        }
    }

@router.post("/create-payment-intent")
def create_payment_intent(
    amount: int,  # Amount in cents
    current_user: User = Depends(get_current_user)
):
    try:
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency="usd",
            metadata={
                "user_id": current_user.id,
                "user_email": current_user.email
            }
        )
        
        return {
            "client_secret": intent.client_secret,
            "payment_intent_id": intent.id
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(request: dict):
    """Handle Stripe webhooks for payment processing"""
    try:
        # In production, verify the webhook signature
        event = request
        
        if event["type"] == "payment_intent.succeeded":
            payment_intent = event["data"]["object"]
            user_id = payment_intent["metadata"]["user_id"]
            amount = payment_intent["amount"] / 100  # Convert from cents
            
            # Add credit to user account (implement credit system)
            # This would require adding a credits table/field to track user balance
            
            return {"status": "success"}
        
        return {"status": "ignored"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/pricing")
def get_pricing():
    """Get current pricing information"""
    return {
        "notebooks": {
            "cpu": {
                "price_per_hour": 0.30,
                "description": "2 CPU cores, 8GB RAM"
            },
            "tesla-t4": {
                "price_per_hour": 1.20,
                "description": "Tesla T4 GPU, 4 CPU cores, 16GB RAM"
            },
            "tesla-v100": {
                "price_per_hour": 3.00,
                "description": "Tesla V100 GPU, 8 CPU cores, 32GB RAM"
            },
            "rtx-4090": {
                "price_per_hour": 1.80,
                "description": "RTX 4090 GPU, 6 CPU cores, 24GB RAM"
            }
        },
        "deployments": {
            "cpu": {
                "price_per_hour": 0.10,
                "price_per_request": 0.001,
                "description": "CPU inference endpoint"
            },
            "gpu-t4": {
                "price_per_hour": 0.60,
                "price_per_request": 0.01,
                "description": "GPU T4 inference endpoint"
            }
        },
        "storage": {
            "price_per_gb_month": 0.05,
            "description": "Model storage and notebook data"
        }
    }