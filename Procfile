web: gunicorn stablecoin.wsgi 
worker: celery -A stablecoin worker -l INFO --concurrency 2
