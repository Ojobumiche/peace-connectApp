# Celery app is imported lazily so Django's runserver works
# even when Redis is not running locally.
try:
    from .celery import app as celery_app
    __all__ = ("celery_app",)
except Exception:
    pass
