import logging
from urllib.parse import quote

import requests
from flask import current_app, request, flash, redirect, url_for, render_template, jsonify
from flask_login import login_required, current_user
from flask_mail import Message
from werkzeug.utils import secure_filename

import app
from app.models import Photo, Folder, Friend, User
from app.photo import photo_bp
from app.photo.form import UploadPhotoForm, CreateFolderForm

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

logging.basicConfig(level=logging.DEBUG)

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
    headers = {
        "AccessKey": current_app.config['BUNNY_STORAGE_API_KEY'],
        "Content-Type": "application/octet-stream"
    }
    upload_path = f"{folder_path}/{filename}" if folder_path else filename
    upload_url = f"{get_bunny_storage_base_url()}/{upload_path}"
    response = requests.put(upload_url, data=file, headers=headers)

    if response.status_code == 201:
        file_url = f"{current_app.config['BUNNY_CDN_URL']}/{folder_path}/{filename}" if folder_path else f"{current_app.config['BUNNY_CDN_URL']}/{filename}"
        logging.debug(f"Зображення завантажено: {file_url}")
        return file_url
    else:
        logging.error(f"Помилка завантаження на BunnyCDN: {response.text}")
        return None



def delete_from_bunny(filename, folder_path=""):
    headers = {
        "AccessKey": current_app.config['BUNNY_STORAGE_API_KEY']
    }
    delete_path = f"{folder_path}/{filename}" if folder_path else filename
    delete_url = f"{get_bunny_storage_base_url()}/{delete_path}"
    response = requests.delete(delete_url, headers=headers)
    return response.status_code == 200


def create_folder_in_bunny(folder_path):
    headers = {
        "AccessKey": current_app.config['BUNNY_STORAGE_API_KEY'],
        "Content-Type": "application/json"
    }

    user_folder_path = f"user_{current_user.id}/{folder_path}"
    folder_path_encoded = quote(user_folder_path)
    create_url = f"{get_bunny_storage_base_url()}/{folder_path_encoded}/"

    logging.debug(f"Створення папки: {create_url}")

    response = requests.put(create_url, headers=headers)
    if response.status_code in [201, 200]:
        return user_folder_path
    else:
        logging.error(f"Помилка створення папки: {response.status_code}, {response.text}")
        return None



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

@photo_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_photo():
    form = UploadPhotoForm()
    folders = Folder.query.filter_by(user_id=current_user.id).all()

    main_folder = Folder.query.filter_by(user_id=current_user.id, name="Основна").first()
    if not main_folder:
        main_folder = Folder(name="Основна", user_id=current_user.id, path="Основна")
        app.db.session.add(main_folder)
        app.db.session.commit()

    if form.validate_on_submit():
        file = form.photo.data
        selected_folder_id = request.form.get("folder_id", type=int)

        selected_folder = Folder.query.get(selected_folder_id) if selected_folder_id else main_folder

        folder_path = selected_folder.path
        create_folder_in_bunny(folder_path)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_url = upload_to_bunny(file.stream.read(), filename, folder_path)

            if file_url:
                photo = Photo(filename=file_url, user_id=current_user.id, folder=selected_folder)
                app.db.session.add(photo)
                app.db.session.commit()

                if selected_folder.id != main_folder.id:
                    duplicate_photo = Photo(filename=file_url, user_id=current_user.id, folder=main_folder)
                    app.db.session.add(duplicate_photo)
                    app.db.session.commit()

                flash('Фото успішно завантажено!', 'success')
                return redirect(url_for('photo.gallery', folder_id=selected_folder.id))
            else:
                flash('Помилка завантаження на Bunny.net!', 'danger')

    return render_template('upload.html', form=form, folders=folders)


@photo_bp.route('/gallery')
@login_required
def gallery():
    folder_id = request.args.get('folder_id', type=int)

    if folder_id:
        photos = Photo.query.filter_by(folder_id=folder_id, user_id=current_user.id).all()
        current_folder = Folder.query.get(folder_id)
    else:
        photos = []
        current_folder = None

    folders = Folder.query.filter_by(parent_id=folder_id, user_id=current_user.id).all()

    friend_ids = Friend.query.with_entities(Friend.friend_id).filter_by(user_id=current_user.id).all()
    friends = User.query.filter(User.id.in_([f[0] for f in friend_ids])).all()

    return render_template('gallery.html',
                           photos=photos,
                           folders=folders,
                           current_folder=current_folder,
                           friends=friends,
                           )


@photo_bp.route('/delete_photo/<int:photo_id>', methods=['POST'])
@login_required
def delete_photo(photo_id):
    photo = Photo.query.get(photo_id)
    if photo and photo.user_id == current_user.id:
        filename = photo.filename.split('/')[-1]
        folder_path = photo.folder.path if photo.folder else ""
        if delete_from_bunny(filename, folder_path):
            app.db.session.delete(photo)
            app.db.session.commit()
            flash('Фото успішно видалено!', 'success')
        else:
            flash('Помилка видалення з Bunny.net!', 'danger')
    else:
        flash('Фото не знайдено або у вас немає прав на його видалення.', 'danger')
    return redirect(url_for('photo.gallery', folder_id=photo.folder.id if photo.folder else None))


@photo_bp.route('/create_folder', methods=['GET', 'POST'])
@login_required
def create_folder():
    form = CreateFolderForm()
    if form.validate_on_submit():
        parent_id = request.form.get("parent_id", type=int)
        parent_folder = Folder.query.get(parent_id) if parent_id else None
        folder_name = form.name.data

        folder_path = f"{parent_folder.path}/{folder_name}" if parent_folder else folder_name
        if create_folder_in_bunny(folder_name):
            new_folder = Folder(
                name=folder_name,
                user_id=current_user.id,
                parent=parent_folder,
                path=f"user_{current_user.id}/{folder_name}"
            )
            app.db.session.add(new_folder)
            app.db.session.commit()
            flash('Папка створена!', 'success')
        else:
            flash('Не вдалося створити папку на BunnyCDN.', 'danger')

        return redirect(url_for('photo.gallery', folder_id=parent_id if parent_folder else None))

    return render_template('create_folder.html', form=form)


@photo_bp.route('/share_photo/<int:photo_id>', methods=['GET', 'POST'])
@login_required
def share_photo(photo_id):
    photo = Photo.query.get(photo_id)
    if not photo or photo.user_id != current_user.id:
        flash("Фото не знайдено або ви не маєте прав на його поширення.", "danger")
        return redirect(url_for('photo.gallery'))

    friend_ids = Friend.query.with_entities(Friend.friend_id).filter_by(user_id=current_user.id).all()
    friends = User.query.filter(User.id.in_([f[0] for f in friend_ids])).all()

    if request.method == 'POST':
        selected_friends = request.form.getlist('friends')
        for friend_id in selected_friends:
            share_photo_with_friend(photo.id, int(friend_id))
        flash("Фото успішно поширено!", "success")
        return redirect(url_for('photo.gallery'))

    return render_template('share_photo.html', photo=photo, friends=friends)