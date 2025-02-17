from flask import Blueprint

photo_bp = Blueprint("photo", __name__, template_folder="templates")

from app.photo import views
