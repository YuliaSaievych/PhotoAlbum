import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True

    # Bunny.net storage settings
    BUNNY_STORAGE_API_KEY = '8bae990f-416f-40c8-8f7340e99f65-13e8-4811'
    BUNNY_STORAGE_ZONE = 'flaskproject'
    BUNNY_STORAGE_REGION = 'de'
    BUNNY_CDN_URL = 'https://flask.b-cdn.net'


