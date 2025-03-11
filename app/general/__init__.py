from flask import Blueprint

general_bp = Blueprint("general", __name__, template_folder="templates")

from app.general import views
