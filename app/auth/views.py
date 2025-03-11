import os
import random
import string
import uuid
from datetime import datetime

import requests
from flask import redirect, flash, url_for, render_template, request, session, current_app
from flask_bcrypt import generate_password_hash
from flask_login import current_user, login_user, login_required, logout_user
from flask_mail import Message

from app import db, mail
from app.models import User
from . import auth_bp
from .form import RegisterForm, LoginForm, OTPForm, RecoverPasswordForm, ResetPasswordForm
from .utils import generate_otp, send_reset_password_email


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

        captcha_response = request.form.get('g-recaptcha-response')

        secret_key = "6LcYS8sqAAAAAMcWg-Nl-Zk3HX7MlQU_pJKQf-TJ"
        payload = {
            'secret': secret_key,
            'response': captcha_response
        }
        response = requests.post("https://www.google.com/recaptcha/api/siteverify", data=payload)
        result = response.json()

        if not result['success']:
            flash('Пройдіть перевірку reCAPTCHA.', 'danger')
            return redirect(url_for('auth.register'))

        existing_user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.email.data)).first()
        if existing_user:
            flash('Ім\'я користувача або електронна пошта вже використовуються. Будь ласка, виберіть інші.', 'danger')
            return redirect(url_for('auth.register'))

        activation_token = str(uuid.uuid4())
        new_user = User(username=form.username.data, email=form.email.data, image_file='')
        new_user.activation_token = activation_token
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        new_user.create_main_folder()


        send_activation_email(new_user.email, activation_token)
        flash('На вашу електронну пошту відправлено лист для активації облікового запису.', 'success')

        flash(f'Користувача {form.username.data} створено', 'success')
        return redirect(url_for("auth.login"))
    else:
        print("Form errors:", form.errors)
    return render_template('register.html',
                           form=form,
                           title="Register",
                           os_info=os.name,
                           user_agent="Sample User Agent",
                           current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                           is_authenticated=current_user.is_authenticated)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    errors = []
    form = LoginForm()
    recover_form = RecoverPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None:
            flash('Користувача не знайдено. Зареєструйтесь.', 'danger')
            return redirect(url_for('auth.register'))
        elif not user.check_password(form.password.data):
            flash('Невірний пароль.', 'danger')
            return redirect(url_for('auth.login'))
        elif not user.is_active:
            flash('Ваш обліковий запис не активовано. Перевірте свою електронну пошту.', 'danger')
            return redirect(url_for('auth.login'))

        if user.option_enabled:
            otp = generate_otp()
            session['otp'] = otp
            session['user_email'] = user.email
            send_otp_email(user.email, otp)
            flash('Перевірте свою пошту для OTP.')
            return redirect(url_for('auth.verify_otp'))
        else:
            login_user(user, remember=form.remember.data)
            flash('Вхід успішний!', 'success')
            return redirect(url_for('user.account'))

    return render_template('login.html',
                           form=form,
                           recover_form=recover_form,
                           title="Login",
                           os_info=os.name,
                           user_agent="Sample User Agent",
                           current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                           is_authenticated=current_user.is_authenticated)


@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    user_data = session.pop('user_data', current_user.id)
    logout_user()
    flash('Ви вийшли з системи', 'success')
    return redirect(url_for('auth.login', user_data=user_data))


@auth_bp.route('/activate/<token>')
def activate(token):
    user = User.query.filter_by(activation_token=token).first()
    if user:

        print(f"Активація користувача: {user.email}")
        user.is_active = True
        user.activation_token = None
        db.session.commit()
        flash("Ваш акаунт активовано! Тепер ви можете увійти в систему.")
    else:
        print(f"Помилка вктивації. Токен не знайдено: {token}")
        flash("Недійсний або прострочений токен активації.")
    return redirect(url_for('auth.login'))


def send_activation_email(email, token):
    activation_link = url_for('auth.activate', token=token, _external=True)
    msg = Message(
        'Активація акаунту',
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[email]
    )
    msg.body = f'Перейдіть за посиланням, щоб активувати ваш акаунт: {activation_link}'
    try:
        mail.send(msg)
        print(f"Лист аквації надіслано на {email} з посиланням: {activation_link}")
    except Exception as e:
        print(f"Помилка надсилання листа: {e}")


@auth_bp.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    form = OTPForm()
    if form.validate_on_submit():
        otp = form.otp.data
        if otp == session.get('otp'):
            user = User.query.filter_by(email=session.get('user_email')).first()
            if user:
                login_user(user)
                session.pop('otp', None)
                session.pop('user_email', None)
                flash('Вхід успішний!', 'success')
                return redirect(url_for('user.account'))
            else:
                flash('Користувача не знайдено.', 'danger')
        else:
            flash('Неправильний OTP. Спробуйте ще раз.', 'danger')
    return render_template('verify_otp.html', form=form)


def send_otp_email(email, otp):
    msg = Message("Ваш код OTP", recipients=[email], sender='flaskserver4@gmail.com')
    msg.body = f"Ваш код {otp}. Будь ласка, використайте його для входу."
    try:
        mail.send(msg)
        print(f"OTP відправлено на {email}")
    except Exception as e:
        print(f"Помилка відправлення: {e}")


@auth_bp.route('/recover', methods=['GET', 'POST'])
def recover():
    form = LoginForm()
    recover_form = RecoverPasswordForm()
    show_recover_form = False

    if recover_form.validate_on_submit():
        email = recover_form.email.data
        user = User.query.filter_by(email=email).first()

        if user:
            token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))

            user.recover_token = token
            db.session.commit()

            send_reset_password_email(email, token)

            flash('Посилання на відновлення паролю надіслано на вашу електронну адресу.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Ця електронна адреса не зареєстрована.', 'danger')
            show_recover_form = True

    return render_template('login.html', recover_form=recover_form, form=form, show_recover_form=show_recover_form)


@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(recover_token=token).first()

    if not user:
        flash('Невірне або прострочене посилання для відновлення паролю.', 'danger')
        return redirect(url_for('auth.login'))

    form = ResetPasswordForm()

    if form.validate_on_submit():
        new_password = form.password.data
        user.password = generate_password_hash(new_password)
        user.recover_token = None
        db.session.commit()

        flash('Пароль успішно змінено.', 'success')
        return redirect(url_for('auth.login'))

    print(f"Токен відновлення: {token}")
    return render_template('reset_password.html', form=form, token=token)