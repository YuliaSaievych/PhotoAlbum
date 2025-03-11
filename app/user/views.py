import datetime
import os

import pyotp
from flask import render_template, request, current_app, url_for, flash, redirect
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.auth.form import LoginForm, RegisterForm
from app.models import User, Friend, Photo, Folder
from app.user import user_bp
from app.user.form import ChangePasswordForm, UpdateAccountForm


@user_bp.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    main_folder = Folder.query.filter_by(name="Основна", user_id=current_user.id).first()

    if main_folder:
        photos = Photo.query.filter_by(folder_id=main_folder.id, user_id=current_user.id).all()
    else:
        photos = []

    user_id = request.args.get("user_id", type=int)

    if user_id and user_id != current_user.id:
        user = User.query.get(user_id)
        if not user:
            flash("Користувача не знайдено!", "danger")
            return redirect(url_for("user.account"))
        is_own_profile = False
    else:
        user = current_user
        is_own_profile = True

    friends = User.query.join(Friend, ((Friend.user_id == user.id) & (Friend.friend_id == User.id)) |
                              ((Friend.friend_id == user.id) & (Friend.user_id == User.id))) \
        .filter(Friend.status == "accepted").all()

    friend_requests = []
    if is_own_profile:
        friend_requests = User.query.join(Friend, Friend.user_id == User.id) \
            .filter(Friend.friend_id == user.id, Friend.status == "pending").all()

    if request.method == 'POST':
        if 'enable_2fa' in request.form:
            if not user.two_factor_enabled:
                totp = pyotp.random_base32()
                user.two_factor_secret = totp
                user.two_factor_enabled = True
                db.session.commit()
                flash('2FA увімкнено. Використовуйте Google Authenticator або інший TOTP додаток.', 'success')
        elif 'disable_2fa' in request.form:
            user.two_factor_enabled = False
            user.two_factor_secret = None
            db.session.commit()
            flash('2FA вимкнено.', 'success')

    login_form = LoginForm()
    register_form = RegisterForm()

    return render_template('account.html',
                           user=user,
                           is_own_profile=is_own_profile,
                           os_info=os.name,
                           user_agent=request.user_agent.string,
                           current_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                           is_authenticated=current_user.is_authenticated,
                           friends=friends,
                           friend_requests=friend_requests,
                           login_form=login_form,
                           register_form=register_form,
                           photos=photos
                           )



@user_bp.route('/change_data', methods=['GET', 'POST'])
@login_required
def change_data():
    data = [os.name, datetime.datetime.now(), request.user_agent]
    account_form = UpdateAccountForm(obj=current_user)
    password_form = ChangePasswordForm()

    if account_form.validate_on_submit():
        current_user.username = account_form.username.data
        current_user.email = account_form.email.data
        current_user.last_seen = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if account_form.profile_picture.data:
            profile_picture = account_form.profile_picture.data
            filename = secure_filename(profile_picture.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            profile_picture.save(filepath)
            current_user.image_file = filename

        db.session.commit()

        flash('Твій профіль оновлено!', 'success')
        return redirect(url_for('user.account'))

    elif password_form.validate_on_submit():
        current_user.set_password(password_form.new_password.data)
        current_user.last_seen = datetime.datetime.now()
        db.session.commit()

        flash('Пароль змінено!', 'success')
        return redirect(url_for('user.account'))

    if 'enable_2fa' in request.form:
        current_user.option_enabled = True
        db.session.commit()
        flash('2FA увімкнено. Під час наступного входу використовуйте OTP.', 'success')
    elif 'disable_2fa' in request.form:
        current_user.option_enabled = False
        db.session.commit()
        flash('2FA вимкнено.', 'success')

    return render_template('change_data.html',
                           form=account_form,
                           password_form=password_form,
                           data=data,
                           user=current_user,
                           os_info=os.name,
                           user_agent="Sample User Agent",
                           current_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                           is_authenticated=current_user.is_authenticated
                           )


@user_bp.route('/enable_2fa', methods=['GET', 'POST'])
@login_required
def enable_2fa():
    user = current_user
    if not user.two_factor_secret:
        user.generate_2fa_secret()

    totp = pyotp.TOTP(user.two_factor_secret)
    totp_uri = totp.provisioning_uri(name=user.email, issuer_name="MyApp")

    return render_template('change_data.html', totp_uri=totp_uri)


@user_bp.route('/toggle_option', methods=['POST'])
@login_required
def toggle_option():
    current_user.option_enabled = not current_user.option_enabled
    db.session.commit()
    flash('2FA успішно змінено.', 'success')
    return redirect(url_for('user.account'))
