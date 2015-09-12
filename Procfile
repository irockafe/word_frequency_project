web: gunicorn word_frequency_ru:app --log-file=- 
worker: celery worker --app=tasks.app
