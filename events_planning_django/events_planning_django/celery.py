import os
from celery import Celery
from django.conf import settings
import logging.config
# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'events_planning_django.settings')

app = Celery('events_planning_django')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')


if hasattr(settings, "LOGGING"):
    logging.config.dictConfig(settings.LOGGING)


logger = logging.getLogger("app")
# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# @app.task(bind=True)
# def check_schedule(self):
#     logger.info("beep")
#     print("beep (print fallback)")

app.conf.beat_schedule = {
    'release_expired_tickets_every_minute': {
        'task': 'app.tasks.release_expired_tickets',
        'schedule': 60.0, 
    },
    'debug_heartbeat': {
        'task': 'events_planning_django.celery.check_schedule',
        'schedule': 5.0,  
    },
}
app.conf.timezone = 'UTC'