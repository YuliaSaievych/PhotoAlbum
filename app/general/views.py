import datetime
import os

from flask import render_template
from flask_login import current_user

from app.auth.form import RegisterForm
from app.general import general_bp


@general_bp.route('/')
def home():
    form = RegisterForm()
    return render_template('home.html',
                           form=form,
                           register_form=form,
                           is_authenticated=current_user.is_authenticated
                           )
