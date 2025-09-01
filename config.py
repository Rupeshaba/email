import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_very_secret_key_that_should_be_changed_in_production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0'
    CELERY_IMPORTS = ('app.email_utils',) # Specify modules containing Celery tasks
    TELEGRAM_BOT_TOKEN = os.environ.get('8309194161:AAHwrChFv2aACvdRIvTfgVyp6Bl00_ewlO4')
    TELEGRAM_CHAT_ID = os.environ.get('1248118664')
