import logging
from urllib.parse import quote

import requests
from flask import current_app
from flask_login import current_user
from flask_mail import Message

import app
from app.models import Photo, Folder, User, FolderAccess

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def send_email(to, subject, body):
    msg = Message(subject, recipients=[to], body=body, sender=current_app.config['MAIL_DEFAULT_SENDER'])
    try:
        app.mail.send(msg)
        logging.debug(f"Лист успішно надіслано на {to}")
    except Exception as e:
        logging.error(f"Помилка надсилання листа: {e}")

def get_bunny_storage_base_url():
    return f"https://storage.bunnycdn.com/{current_app.config['BUNNY_STORAGE_ZONE']}"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_to_bunny(file, filename, folder_path=""):
    access_key = current_app.config.get('BUNNY_STORAGE_API_KEY')
    storage_zone = current_app.config.get('BUNNY_STORAGE_ZONE')

    if not access_key or not storage_zone:
        logging.error("BunnyCDN API ключ або зона зберігання не налаштовані.")
        return None

    headers = {
        "AccessKey": access_key,
        "Content-Type": "application/json"
    }
    upload_path = f"{folder_path}/{filename}" if folder_path else filename
    upload_url = f"{get_bunny_storage_base_url()}/{upload_path}"
    logging.debug(f"Завантаження на {upload_url}...")

    try:
        response = requests.put(upload_url, data=file, headers=headers, timeout=10)
        if response.status_code == 201:
            file_url = f"https://{current_app.config['BUNNY_CDN_URL']}/{folder_path}/{filename}" if folder_path else f"https://{current_app.config['BUNNY_CDN_URL']}/{filename}"
            logging.debug(f"File URL: {file_url}")
            return file_url
        else:
            logging.error(f"Помилка завантаження на хмару: {response.status_code}, {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Мережева помилка під час завантаження: {e}")
        return None


def delete_from_bunny(filename, folder_path=""):
    access_key = current_app.config.get('BUNNY_STORAGE_API_KEY')
    storage_zone = current_app.config.get('BUNNY_STORAGE_ZONE')

    if not access_key or not storage_zone:
        logging.error("BunnyCDN API ключ або зона зберігання не налаштовані.")
        return False

    headers = {
        "AccessKey": access_key
    }

    delete_path = quote(
        f"user_{current_user.id}/{folder_path}/{filename}" if folder_path else f"user_{current_user.id}/{filename}")
    delete_url = f"{get_bunny_storage_base_url()}/{delete_path}"

    logging.debug(f"Видалено з хмари: {delete_url}")

    try:
        logging.debug(f"Спроба видалення файлу: {delete_url}")
        response = requests.delete(delete_url, headers=headers)
        logging.debug(f"Відповідь від сервера: {response.status_code}, {response.text}")
        if response.status_code in [200, 204]:
            logging.debug(f"Файл {filename} успішно видалено з хмари.")
            return True
        elif response.status_code == 404:
            logging.warning(f"Файл {filename} не знайдено на хмарі.")
            return True
        else:
            logging.error(f"Помилка видалення {filename}: {response.status_code}, {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        logging.error(f"Мережева помилка під час видалення: {e}")
        return False


def create_folder_in_bunny(folder_path):
    access_key = current_app.config.get('BUNNY_STORAGE_API_KEY')
    storage_zone = current_app.config.get('BUNNY_STORAGE_ZONE')

    if not access_key or not storage_zone:
        logging.error("BunnyCDN API ключ або зона зберігання не налаштовані.")
        return None

    headers = {
        "AccessKey": access_key,
        "Content-Type": "application/json"
    }

    user_folder_path = quote(f"user_{current_user.id}/{folder_path}")
    create_url = f"{get_bunny_storage_base_url()}/{user_folder_path}/"

    logging.debug(f"Створення папки: {create_url}")

    try:
        response = requests.put(create_url, headers=headers)
        if response.status_code in [201, 200]:
            return user_folder_path
        else:
            logging.error(f"Помилка створення папки: {response.status_code}, {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Мережева помилка під час створення папки: {e}")
        return None


def delete_folder_from_bunny(folder_path):
    access_key = current_app.config.get('BUNNY_STORAGE_API_KEY')
    storage_zone = current_app.config.get('BUNNY_STORAGE_ZONE')

    if not access_key or not storage_zone:
        logging.error("BunnyCDN API ключ або зона зберігання не налаштовані.")
        return False

    headers = {
        "AccessKey": access_key
    }

    delete_path = quote(f"user_{current_user.id}/{folder_path}")
    delete_url = f"{get_bunny_storage_base_url()}/{delete_path}"

    logging.debug(f"Видалення папки з хмари: {delete_url}")

    try:
        response = requests.delete(delete_url, headers=headers)
        if response.status_code in [200, 204]:
            logging.debug(f"Папка {folder_path} успішно видалена з хмари.")
            return True
        elif response.status_code == 404:
            logging.warning(f"Папка {folder_path} не знайдена на хмари.")
            return True
        else:
            logging.error(f"Помилка видалення папки {folder_path}: {response.status_code}, {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        logging.error(f"Мережева помилка під час видалення папки: {e}")
        return False

def share_photo_with_friend(photo_id, friend_id):
    photo = Photo.query.get(photo_id)
    friend = User.query.get(friend_id)

    if not photo or not friend:
        return False

    shared_folder = Folder.query.filter_by(user_id=friend.id, name="Поширені").first()
    if not shared_folder:
        shared_folder = Folder(name="Поширені", user_id=friend.id, path=f"user_{friend.id}/Поширені")
        app.db.session.add(shared_folder)
        app.db.session.commit()
        create_folder_in_bunny(shared_folder.path)

    shared_photo = Photo(filename=photo.filename, user_id=friend.id, folder=shared_folder)
    app.db.session.add(shared_photo)
    app.db.session.commit()

    email_subject = "Вам поширили фото!"
    email_body = f"{current_user.username} поділився з вами фото. Переглянути його можна тут: {photo.filename}"
    send_email(friend.email, email_subject, email_body)

    return True


def share_folder_with_friend(folder_id, friend, access_level='viewer'):
    access_record = FolderAccess.query.filter_by(folder_id=folder_id, user_id=friend.id).first()
    if not access_record:
        new_access = FolderAccess(folder_id=folder_id, user_id=friend.id, access_level=access_level)
        app.db.session.add(new_access)
        logging.debug(f"Додано доступ для користувача {friend.username} до папки {folder_id}")

    folder = Folder.query.get(folder_id)
    if folder:
        if friend not in folder.shared_with:
            folder.shared_with.append(friend)

        app.db.session.commit()
    else:
        logging.error(f"Папка з ID {folder_id} не знайдена.")


def notify_shared_users(users, folder):

    if not isinstance(users, list):
        users = [users]

    for user in users:
        msg = Message(
            'Папку поширено',
            sender='MAIL_USERNAME',
            recipients=[user.email]
        )
        msg.body = f"Вітаємо, {user.username}!\n\nВам було поширено папку '{folder.name}'. Ви можете побачити її в своїй галереї."
        try:
            app.mail.send(msg)
            logging.debug(f"Лист успішно надіслано на {user.email}")
        except Exception as e:
            logging.error(f"Помилка надсилання листа: {e}")