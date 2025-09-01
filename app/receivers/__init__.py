from flask import Blueprint

bp = Blueprint('receivers', __name__)

from app.receivers import routes
