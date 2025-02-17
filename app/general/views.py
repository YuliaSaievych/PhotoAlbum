import datetime
import os

from flask import render_template, redirect, request, url_for
from flask_login import current_user

from app.general import general_bp


@general_bp.route('/')
def home():
    return render_template('home.html',
                           os_info=os.name,
                           user_agent="Sample User Agent",
                           current_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                           is_authenticated=current_user.is_authenticated
                           )


def render_account_template(template_name, **kwargs):
    if request.referrer and 'account' in request.referrer:
        return render_template(template_name, **kwargs)
    else:
        return redirect(url_for('user.account'))
