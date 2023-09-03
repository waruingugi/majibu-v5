release: ./release_tasks.sh
web: uvicorn usgi:app --reload --host=0.0.0.0 --port=${PORT:-5000}
worker: celery -A app.worker worker -Q scheduler-queue -l info
beat: celery -A app.worker beat