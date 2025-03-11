import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True

    BUNNY_STORAGE_API_KEY = '5dea2cab-ab5a-4600-b6b00166a804-2972-4f72'
    BUNNY_STORAGE_ZONE = 'photozone'
    BUNNY_STORAGE_REGION = 'de'
    BUNNY_CDN_URL = 'photozone1.b-cdn.net'


