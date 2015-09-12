web: gunicorn word_frequency_app_ru:app --log-file=-
worker: celery -A word_frequency_app_ru.celery worker
