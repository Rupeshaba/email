from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet
import os

# Generate a key for Fernet encryption. In a real application, this should be loaded from a secure environment variable.
# For development, we'll generate one if not present.
if os.environ.get('FERNET_KEY') is None:
    FERNET_KEY = Fernet.generate_key().decode('utf-8')
    print(f"Generated FERNET_KEY: {FERNET_KEY}. Please add this to your .env file for production.")
else:
    FERNET_KEY = os.environ.get('FERNET_KEY')

cipher_suite = Fernet(FERNET_KEY.encode('utf-8'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class SenderEmail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    _password_encrypted = db.Column(db.LargeBinary, nullable=False)
    sent_count = db.Column(db.Integer, default=0)
    sending_limit = db.Column(db.Integer, default=500) # Default limit

    @property
    def password(self):
        return cipher_suite.decrypt(self._password_encrypted).decode('utf-8')

    @password.setter
    def password(self, plaintext_password):
        self._password_encrypted = cipher_suite.encrypt(plaintext_password.encode('utf-8'))

class ReceiverEmail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(20), default='pending') # pending, sent, failed
    sent_at = db.Column(db.DateTime, nullable=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=True)

class MessageTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    body_html = db.Column(db.Text, nullable=False)
    body_plain = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=False)

class LogEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    level = db.Column(db.String(20)) # INFO, WARNING, ERROR
    message = db.Column(db.Text, nullable=False)
    sender_email = db.Column(db.String(120), nullable=True)
    receiver_email = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(20), nullable=True) # success, failure
    error_reason = db.Column(db.Text, nullable=True)

class TelegramSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bot_token = db.Column(db.String(255), nullable=False)
    chat_id = db.Column(db.String(255), nullable=False)
    alerts_enabled = db.Column(db.Boolean, default=True)
    alert_login_success = db.Column(db.Boolean, default=True)
    alert_login_failure = db.Column(db.Boolean, default=True)
    alert_sending_started = db.Column(db.Boolean, default=True)
    alert_sending_paused_resumed_stopped = db.Column(db.Boolean, default=True)
    alert_batch_sent = db.Column(db.Boolean, default=True)
    alert_errors = db.Column(db.Boolean, default=True)

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='draft') # draft, running, paused, stopped, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    total_emails = db.Column(db.Integer, default=0)
    emails_sent = db.Column(db.Integer, default=0)
    emails_failed = db.Column(db.Integer, default=0)
    template_id = db.Column(db.Integer, db.ForeignKey('message_template.id'), nullable=True)

    receivers = db.relationship('ReceiverEmail', backref='campaign', lazy='dynamic')
