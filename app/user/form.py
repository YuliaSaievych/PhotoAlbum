from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms.fields.simple import StringField, PasswordField, FileField, SubmitField
from wtforms.validators import Regexp, Length, DataRequired, EqualTo, Email, ValidationError

from app.models import User


class UpdateAccountForm(FlaskForm):
    username = StringField('Ім\'я', validators=[
        DataRequired(),
        Length(min=4, max=14, message="This required field must be between 4 and 14 characters long"),
        Regexp(r'^[A-Za-z .]+$', message='The username can contain only Latin letters, spaces and periods.')
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message="This is a required field")])
    profile_picture = FileField('Profile picture', validators=[
        FileAllowed(['jpg', 'png'], 'Only files with the extension .jpg або .png.')
    ])

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('This username is already taken. Please select another one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('This email is already in use. Please select another one.')

    submit = SubmitField('Update your profile')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old password', validators=[DataRequired()])
    new_password = PasswordField('New password',
                                 validators=[Length(min=6, message="Password must be more than 6 characters")])
    confirm_new_password = PasswordField('Repeat your new password',
                                         validators=[EqualTo('new_password', message='Passwords must be the same')])
    submit_change_password = SubmitField('Change Password')


