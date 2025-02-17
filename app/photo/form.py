from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from wtforms.fields.simple import StringField
from wtforms.validators import DataRequired

class UploadPhotoForm(FlaskForm):
    photo = FileField('Photo', validators=[DataRequired()])
    submit = SubmitField('Upload')

    def __init__(self, *args, **kwargs):
        super(UploadPhotoForm, self).__init__(*args, **kwargs)

class CreateFolderForm(FlaskForm):
    name = StringField('Назва папки', validators=[DataRequired()])
    submit = SubmitField('Створити')