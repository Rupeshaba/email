from flask import Blueprint

bp = Blueprint('sending', __name__)

from app.sending import routes
