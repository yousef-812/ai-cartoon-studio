from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "ai_cartoon_studio",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.story", "app.tasks.script", "app.tasks.direction"],
)
celery_app.conf.update(
    broker_connection_retry_on_startup=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    task_always_eager=settings.celery_task_always_eager,
    task_eager_propagates=True,
    worker_prefetch_multiplier=1,
)
