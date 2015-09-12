web: gunicorn word_frequency_app_ru:app --log-file=- 
worker: celery worker --app=word_frequency_app_ru.app
