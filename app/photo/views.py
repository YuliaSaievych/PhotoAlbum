import logging

import requests
from flask import current_app, request, flash, redirect, url_for, render_template
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

import app
from app.models import Photo, Folder
from app.photo import photo_bp
from app.photo.form import UploadPhotoForm, CreateFolderForm

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

logging.basicConfig(level=logging.DEBUG)

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
        "AccessKey": current_app.config['BUNNY_STORAGE_API_KEY']
    }
    create_url = f"{get_bunny_storage_base_url()}/{folder_path}/"

    response = requests.put(create_url, headers=headers)
    if response.status_code in [201, 200]:
        return True
    return False


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

    return render_template('gallery.html', photos=photos, folders=folders, current_folder=current_folder)


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
        if create_folder_in_bunny(folder_path):
            new_folder = Folder(
                name=folder_name,
                user_id=current_user.id,
                parent=parent_folder,
                path=folder_path
            )
            app.db.session.add(new_folder)
            app.db.session.commit()
            print('Папка створена')
            flash('Папка створена!', 'success')
        else:
            flash('Не вдалося створити папку на BunnyCDN.', 'danger')

        return redirect(url_for('photo.gallery', folder_id=parent_id if parent_folder else None))

    return render_template('create_folder.html', form=form)
