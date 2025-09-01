from flask import Blueprint

bp = Blueprint('senders', __name__)

from app.senders import routes
