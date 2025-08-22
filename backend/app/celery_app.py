from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

# Create Celery app
celery_app = Celery(
    "ml_platform",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379"),
    include=["app.tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,
    task_routes={
        "app.tasks.cleanup_stopped_notebooks": {"queue": "cleanup"},
        "app.tasks.calculate_usage_costs": {"queue": "billing"},
    },
)

# Periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-notebooks": {
        "task": "app.tasks.cleanup_stopped_notebooks",
        "schedule": 300.0,  # Run every 5 minutes
    },
    "calculate-costs": {
        "task": "app.tasks.calculate_usage_costs",
        "schedule": 3600.0,  # Run every hour
    },
}