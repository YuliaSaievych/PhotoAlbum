from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms.fields.simple import StringField, PasswordField, FileField, SubmitField
from wtforms.validators import Regexp, Length, DataRequired, EqualTo, Email, ValidationError

from app.models import User


class UpdateAccountForm(FlaskForm):
    username = StringField('Ім\'я', validators=[
        DataRequired(),
        Length(min=4, max=14, message="Це обов'язкове поле має містити від 4 до 14 символів"),
        Regexp(r'^[A-Za-z .]+$', message='Ім\'я користувача може містити лише латинські літери, пробіли та крапки.')
    ])
    email = StringField('Електронна адреса', validators=[
        DataRequired(),
        Email(message="Це обов'язкове для заповнення поле")])
    profile_picture = FileField('Фото профілю', validators=[
        FileAllowed(['jpg', 'png'], 'Тільки файли з розширенням .jpg або .png')
    ])

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Це ім\'я користувача вже зайнято. Будь ласка, виберіть інше.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Ця електронна адреса вже використовується. Будь ласка, виберіть іншу.')

    submit = SubmitField('Оновіть свій профіль')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Старий пароль', validators=[DataRequired()])
    new_password = PasswordField('Новий пароль',
                                 validators=[Length(min=6, message="Пароль повинен містити більше 6 символів")])
    confirm_new_password = PasswordField('Повторіть новий ',
                                         validators=[EqualTo('new_password', message='Паролі повинні бути однаковими')])
    submit_change_password = SubmitField('Змінити пароль')


