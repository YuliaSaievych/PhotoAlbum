import os

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
mail = Mail()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'abcdcdb'
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'flaskserver4@gmail.com'
    app.config['MAIL_PASSWORD'] = 'bjor symu vtju rgyd'
    app.config['MAIL_DEFAULT_SENDER'] = 'flaskserver@gmail.com'

    bcrypt.init_app(app)
    db.init_app(app)
    migrate = Migrate(app, db)
    login_manager.init_app(app)
    mail.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.models import User

    from .auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from .general import general_bp
    app.register_blueprint(general_bp)

    from .user import user_bp
    app.register_blueprint(user_bp)

    from .photo import photo_bp
    app.register_blueprint(photo_bp, url_prefix='/photo')

    from .friend import friend_bp
    app.register_blueprint(friend_bp)

    return app
