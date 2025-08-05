from celery import Celery
from app.core.config import settings

# Create Celery instance
celery_app = Celery(
    "resume-hithub",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.resume_tasks",
        "app.tasks.github_tasks",
        "app.tasks.matching_tasks"
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,  # Results expire after 1 hour
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
    task_soft_time_limit=240,  # Soft limit at 4 minutes
    worker_prefetch_multiplier=1,  # Don't prefetch tasks
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks
)

# Task routing (optional)
celery_app.conf.task_routes = {
    "app.tasks.resume_tasks.*": {"queue": "resume_processing"},
    "app.tasks.github_tasks.*": {"queue": "github_processing"},
    "app.tasks.matching_tasks.*": {"queue": "matching"},
}

# Rate limits for external API calls
celery_app.conf.task_annotations = {
    "app.tasks.github_tasks.analyze_github_profile": {
        "rate_limit": "10/m"  # 10 per minute for GitHub API
    }
}