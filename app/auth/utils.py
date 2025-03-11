import random
import string

from flask import url_for, current_app
from flask_mail import Message

from app import mail

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))


def send_reset_password_email(email, token):
    reset_password_link = url_for('auth.reset_password', token=token, _external=True)
    msg = Message(
        'Відновлення паролю',
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[email]
    )
    msg.body = f'Щоб відновити пароль, натисніть на це посилання: {reset_password_link}'
    try:
        mail.send(msg)
        print(f"Лист надіслано на {email} з посиланням: {reset_password_link}")
    except Exception as e:
        print(f"Помилка надсилання листа: {e}")