from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, FileAllowed
from wtforms import FileField, SubmitField
from wtforms.fields.choices import SelectField
from wtforms.fields.simple import StringField
from wtforms.validators import DataRequired


class UploadPhotoForm(FlaskForm):
    photo = FileField(
        'Зображення',
        validators=[
            FileRequired(),
            FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Дозволені лише зображення (jpg, jpeg, png, gif)')
        ],
        render_kw={"multiple": True}
    )
    folder_id = SelectField('Папка', coerce=int)
    submit = SubmitField('Завантажити')

    def __init__(self, *args, **kwargs):
        super(UploadPhotoForm, self).__init__(*args, **kwargs)
class CreateFolderForm(FlaskForm):
    name = StringField('', validators=[DataRequired()])
    submit = SubmitField('Створити')


class AddUserForm(FlaskForm):
    friend_id = SelectField('Вибрати друга', coerce=int)
    access_level = SelectField('Рівень доступу', choices=[('viewer', 'Перегляд'), ('editor', 'Редагування')])
