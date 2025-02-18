from flask import Blueprint

friend_bp = Blueprint("friend", __name__, template_folder="templates")

from app.friend import views
