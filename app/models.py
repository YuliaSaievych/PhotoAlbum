import hashlib
import os

from flask import current_app
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy.dialects.postgresql import  JSON

from app import db, bcrypt
from flask import url_for

folder_user_association = db.Table('folder_user_association',
    db.Column('folder_id', db.Integer, db.ForeignKey('folder.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(120), unique=False, nullable=False, default='./images/default_profile_picture.jpg')
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128))
    is_active = db.Column(db.Boolean, default=False, nullable=False)
    activation_token = db.Column(db.String(128), nullable=True)
    token_expiration = db.Column(db.DateTime, nullable=True)
    option_enabled = db.Column(db.Boolean, default=False)
    recover_token = db.Column(db.String(32), unique=True, nullable=True)
    photos = db.relationship('Photo', backref='user', lazy=True)
    folders = db.relationship('Folder', backref='user', lazy=True)
    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

    def generate_auth_token(self, expires_in=3600):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token, expiration=3600):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, max_age=expiration)
        except:
            return None
        return User.query.get(data['id'])

    def create_main_folder(self):
        user_folder = os.path.join("user_folders", str(self.id))
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)

    def get_friend_invite_link(self):
        unique_token = hashlib.md5(f"{self.id}-{self.email}".encode()).hexdigest()
        return url_for('friend.invite_friend', token=unique_token, _external=True)


class Photo(db.Model):
    __tablename__ = 'photo'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'), nullable=True)
    upload_date = db.Column(db.DateTime, default=db.func.current_timestamp())


    folder = db.relationship('Folder', back_populates='photos')

    def __repr__(self):
        return f'<Photo {self.filename}>'


class Folder(db.Model):
    __tablename__ = 'folder'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('folder.id'), nullable=True)

    subfolders = db.relationship('Folder', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    shared_with = db.relationship('User', secondary=folder_user_association, backref='shared_folders')
    photos = db.relationship('Photo', back_populates='folder', lazy=True)

    subfolder_ids = db.Column(JSON(db.Integer), default=list)


    def __repr__(self):
        return f"<Folder {self.name} (ID: {self.id})>"

class FolderAccess(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    access_level = db.Column(db.String(10), default='viewer')


class Friend(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default="pending")

    user = db.relationship('User', foreign_keys=[user_id], backref='friend_requests_sent')
    friend = db.relationship('User', foreign_keys=[friend_id], backref='friend_requests_received')

    def accept(self):
        self.status = "accepted"
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class SharedPhoto(db.Model):
    __tablename__ = 'shared_photo'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    photo_id = db.Column(db.Integer, db.ForeignKey('photo.id'), nullable=False)
    shared_date = db.Column(db.DateTime, default=db.func.current_timestamp())

    sender = db.relationship('User', foreign_keys=[sender_id], backref='shared_photos_sent')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='shared_photos_received')
    photo = db.relationship('Photo', backref='shared_instances')
