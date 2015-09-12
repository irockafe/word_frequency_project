#!/bin/bash

gunicorn word_frequency_app_ru:app --log-file=-
celery -A word_frequency_app_ru.celery worker

