from flask import Blueprint

bp = Blueprint('telegram', __name__)

from app.telegram import routes
