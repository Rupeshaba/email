from app import create_app, db, celery
from flask_migrate import Migrate
import os

app = create_app()
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    from app.models import User, SenderEmail, ReceiverEmail, MessageTemplate, LogEntry, TelegramSettings, Campaign
    return {'db': db, 'User': User, 'SenderEmail': SenderEmail, 'ReceiverEmail': ReceiverEmail,
            'MessageTemplate': MessageTemplate, 'LogEntry': LogEntry, 'TelegramSettings': TelegramSettings,
            'Campaign': Campaign}

if __name__ == '__main__':
    # This block is for running the Flask app directly.
    # For production, use a WSGI server like Gunicorn.
    # For Celery worker, run 'celery -A main.celery worker --loglevel=info'
    # For Celery beat, run 'celery -A main.celery beat --loglevel=info'
    port = app.config.get('PORT', 5000)
    app.run(debug=True, host='0.0.0.0', port=port)
