from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

import os

def create_app():
    app = Flask(__name__, template_folder=os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'templates'))
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.senders import bp as senders_bp
    app.register_blueprint(senders_bp, url_prefix='/senders')

    from app.receivers import bp as receivers_bp
    app.register_blueprint(receivers_bp, url_prefix='/receivers')

    from app.templates import bp as templates_bp
    app.register_blueprint(templates_bp, url_prefix='/templates')

    from app.telegram import bp as telegram_bp
    app.register_blueprint(telegram_bp, url_prefix='/telegram')

    from app.settings import bp as settings_bp
    app.register_blueprint(settings_bp, url_prefix='/settings')

    from app.sending import bp as sending_bp
    app.register_blueprint(sending_bp, url_prefix='/sending')

    from app.dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')

    return app

from app import models
