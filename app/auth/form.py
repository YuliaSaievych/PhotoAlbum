from flask_wtf import FlaskForm
from wtforms.fields.simple import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Regexp, Email, EqualTo, ValidationError, Length

from app.models import User


class RegisterForm(FlaskForm):
    username = StringField('Ім\'я користувача', validators=[
        DataRequired(),
        Regexp('^[a-zA-Z0-9_-]{3,20}$',
               message='Ім\'я користувача має бути довжиною 3-20 символів і може містити лише літери, цифри, підкреслення та дефіси.'),
        Regexp('^[^_].*[^_-]$',
               message='Ім\'я користувача не може починатися або закінчуватися підкресленнями або дефісами')
    ])
    password = PasswordField('Пароль', validators=[DataRequired()])
    confirm_password = PasswordField('Підтвердіть пароль', validators=[DataRequired(), EqualTo('password')])
    email = StringField('Електронна пошта', validators=[DataRequired(), Email()])
    submit = SubmitField('Зареєструватися')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Це ім\'я користувача вже використовується')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Ця адреса електронної пошти вже використовується')


class LoginForm(FlaskForm):
    username = StringField('Ім\'я користувача', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember = BooleanField('Запам\'ятати мене')
    submit = SubmitField('Ввійти')

    def validate(self):
        if not super(LoginForm, self).validate():
            return False

        user = User.query.filter_by(username=self.username.data).first()

        if user is None or not user.check_password(self.password.data):
            self.username.errors.append('Невірний логін!')
            self.password.errors.append('Невірний пароль!')
            return False

        return True

    def validate_on_submit(self):
        return self.is_submitted() and self.validate()


class OTPForm(FlaskForm):
    otp = StringField('OTP', validators=[DataRequired()])
    submit = SubmitField('Верифікація OTP')

class RecoverPasswordForm(FlaskForm):
    email = StringField('Електронна адреса', validators=[DataRequired(), Email()])
    submit = SubmitField('Відновити')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('Ця електронна адреса не зареєстрована!')

    def validate_email_submit(self):
        return self.is_submitted() and self.validate()


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Новий пароль', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Змінити пароль')
