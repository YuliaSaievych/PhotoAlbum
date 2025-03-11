import logging

from flask import request, flash, redirect, url_for, render_template
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

import app
from app.models import Photo, Folder, User, Friend, FolderAccess, folder_user_association
from app.photo import photo_bp
from app.photo.form import UploadPhotoForm, CreateFolderForm, AddUserForm
from app.photo.utils import allowed_file, upload_to_bunny, delete_from_bunny, create_folder_in_bunny, \
    share_photo_with_friend, share_folder_with_friend, delete_folder_from_bunny, notify_shared_users

logging.basicConfig(level=logging.DEBUG)


@photo_bp.route('/gallery')
@login_required
def gallery():
    form = CreateFolderForm()
    folder_id = request.args.get('folder_id', type=int)

    main_folder = Folder.query.filter_by(user_id=current_user.id, parent_id=None, name="Основна").first()

    if not main_folder:
        main_folder = Folder(name="Основна", user_id=current_user.id, path=f"user_{current_user.id}/Основна")
        app.db.session.add(main_folder)
        app.db.session.commit()

    if not folder_id:
        folder_id = main_folder.id

    current_folder = Folder.query.get(folder_id) if folder_id else main_folder
    if not current_folder or (
            current_folder.user_id != current_user.id and
            current_user.id not in [user.id for user in current_folder.shared_with] and
            not FolderAccess.query.filter_by(folder_id=current_folder.id, user_id=current_user.id).first()
    ):
        flash("Ви не маєте доступу до цієї папки!", "danger")
        return redirect(url_for('photo.gallery'))

    folders = Folder.query.filter(
        (Folder.user_id == current_user.id) |
        (Folder.shared_with.any(User.id == current_user.id))
    ).all()

    photos = Photo.query.filter(
        (Photo.folder_id == folder_id) & (
                (Photo.user_id == current_user.id) |
                (Photo.folder.has(Folder.shared_with.any(User.id == current_user.id)))
        )
    ).all()

    shared_folders = Folder.query.join(folder_user_association, Folder.id == folder_user_association.c.folder_id) \
        .filter(folder_user_association.c.user_id == current_user.id).all()
    print(f"Папку поширено: {shared_folders}")

    return render_template('gallery.html',
                           photos=photos,
                           main_folder=main_folder,
                           current_folder=current_folder,
                           folders=folders,
                           shared_folders=shared_folders,
                           form=form
                           )


@photo_bp.route('/view_photo/<int:photo_id>')
@login_required
def view_photo(photo_id):
    photo = Photo.query.get(photo_id)

    if not photo or (
            photo.user_id != current_user.id and
            current_user.id not in [user.id for user in photo.folder.shared_with] and
            not FolderAccess.query.filter_by(folder_id=photo.folder_id, user_id=current_user.id).first()
    ):
        flash("Фото не знайдено або ви не маєте прав на його перегляд.", "danger")
        return redirect(url_for('photo.gallery'))

    return render_template('gallery.html', photo=photo)


@photo_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_photo():
    form = UploadPhotoForm()
    personal_folders = Folder.query.filter_by(user_id=current_user.id).all()
    shared_folders = Folder.query.filter(Folder.shared_with.any(User.id == current_user.id)).all()
    print(f"Поширені папки: {shared_folders}")

    folders = []
    for folder in personal_folders + shared_folders:
        access = FolderAccess.query.filter_by(folder_id=folder.id, user_id=current_user.id).first()
        if folder.user_id == current_user.id or (access and access.access_level == 'editor'):
            folders.append(folder)

    form.folder_id.choices = [(folder.id, folder.name) for folder in folders]

    if form.validate_on_submit():
        selected_folder_id = form.folder_id.data
        selected_folder = Folder.query.get(selected_folder_id)

        if not selected_folder or (
                selected_folder.user_id != current_user.id and
                current_user.id not in [user.id for user in selected_folder.shared_with] and
                not FolderAccess.query.filter_by(folder_id=selected_folder.id, user_id=current_user.id).first()
        ):
            flash("Ви не маєте прав на завантаження фото у цю папку.", "danger")
            return redirect(url_for('photo.gallery'))

        files = request.files.getlist('photo')
        uploaded_files = []

        MAX_FILES = 10
        if len(files) > MAX_FILES:
            flash(f'Можна завантажити не більше {MAX_FILES} файлів за раз.', 'danger')
            return redirect(url_for('photo.upload_photo'))

        MAX_FILE_SIZE = 10 * 1024 * 1024
        for file in files:
            if file.content_length > MAX_FILE_SIZE:
                flash(f'Файл {file.filename} занадто великий. Максимальний розмір: 10 MB.', 'danger')
                return redirect(url_for('photo.upload_photo'))

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_data = file.read()

                file.seek(0)
                file_url = upload_to_bunny(file_data, filename, selected_folder.path)

                if file_url:
                    photo = Photo(filename=file_url, user_id=current_user.id, folder=selected_folder)
                    app.db.session.add(photo)
                    uploaded_files.append(filename)
                else:
                    flash(f'Помилка завантаження файлу {filename}!', 'danger')
            else:
                flash(f'Невірний формат файлу {file.filename}.', 'danger')

        if uploaded_files:
            shared_users = selected_folder.shared_with
            if shared_users:
                notify_shared_users(shared_users, selected_folder)

            app.db.session.commit()
            flash(f'{len(uploaded_files)} фото успішно завантажено!', 'success')
            return redirect(url_for('photo.gallery', folder_id=selected_folder.id))

    return render_template('upload.html', form=form, folders=folders)


@photo_bp.route('/delete_photo/<int:photo_id>', methods=['POST'])
@login_required
def delete_photo(photo_id):
    photo = Photo.query.get(photo_id)

    if not photo or (
            photo.user_id != current_user.id and
            not FolderAccess.query.filter_by(folder_id=photo.folder_id, user_id=current_user.id,
                                             access_level='editor').first()
    ):
        flash('Ви не маєте прав на видалення цього фото.', 'danger')
        return redirect(url_for('photo.gallery'))

    filename = photo.filename.split('/')[-1]
    folder_path = photo.folder.path if photo.folder else ""

    if delete_from_bunny(filename, folder_path):
        app.db.session.delete(photo)
        app.db.session.commit()
        flash('Фото успішно видалено!', 'success')
    else:
        flash('Помилка видалення.', 'danger')

    return redirect(url_for('photo.gallery', folder_id=photo.folder.id if photo.folder else None))


@photo_bp.route('/create_folder', methods=['GET', 'POST'])
@login_required
def create_folder():
    form = CreateFolderForm()
    parent_id = request.args.get('parent_id', type=int)
    parent_folder = Folder.query.get(parent_id) if parent_id else None

    if form.validate_on_submit():
        folder_name = form.name.data

        new_folder = Folder(name=folder_name, user_id=current_user.id, parent_id=parent_id)

        if parent_folder:
            new_folder.path = f"{parent_folder.path}/{folder_name}"
            parent_folder.subfolder_ids = parent_folder.subfolder_ids + [
                new_folder.id] if parent_folder.subfolder_ids else [new_folder.id]
            app.db.session.add(parent_folder)
        else:
            new_folder.path = f"user_{current_user.id}/{folder_name}"

        app.db.session.add(new_folder)
        app.db.session.commit()

        create_folder_in_bunny(new_folder.path)

        flash('Папка успішно створена!', 'success')
        return redirect(url_for('photo.gallery', folder_id=new_folder.id))

    return render_template('create_folder.html', form=form, parent_folder=parent_folder, current_folder=None)


@photo_bp.route('/delete_folder/<int:folder_id>', methods=['POST'])
@login_required
def delete_folder(folder_id):
    folder = Folder.query.get(folder_id)

    if not folder or folder.user_id != current_user.id:
        flash("Ви не маєте прав на видалення цієї папки.", "danger")
        return redirect(url_for('photo.gallery'))

    photos = Photo.query.filter_by(folder_id=folder.id).all()
    for photo in photos:
        delete_photo(photo.id)

    subfolders = Folder.query.filter_by(parent_id=folder.id).all()
    for subfolder in subfolders:
        delete_folder(subfolder.id)

    if delete_folder_from_bunny(folder.path):
        app.db.session.delete(folder)
        app.db.session.commit()
        flash("Папка успішно видалена!", "success")
    else:
        flash("Помилка видалення папки.", "danger")

    return redirect(url_for('photo.gallery'))


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


@photo_bp.route('/share_folder/<int:folder_id>', methods=['GET', 'POST'])
@login_required
def share_folder(folder_id):
    folder = Folder.query.get(folder_id)
    if not folder or folder.user_id != current_user.id:
        flash("Папка не знайдена або ви не маєте прав на її поширення.", "danger")
        return redirect(url_for('photo.gallery'))

    friend_ids = Friend.query.with_entities(Friend.friend_id).filter_by(user_id=current_user.id).all()
    friends = User.query.filter(User.id.in_([f[0] for f in friend_ids])).all()

    if request.method == 'POST':
        friend_id = request.form.get('friend_id')
        access_level = request.form.get('access_level', 'viewer')

        if friend_id:
            friend = User.query.get(friend_id)
            if friend:
                share_folder_with_friend(folder.id, friend, access_level)
                notify_shared_users([friend], folder)
                flash(f"Папка поширена для {friend.username} з рівнем доступу: {access_level}.", "success")
            else:
                flash("Користувача не знайдено.", "danger")
        else:
            flash("Будь ласка, виберіть друга.", "danger")

        return redirect(url_for('photo.access_control', folder_id=folder.id))

    return render_template('access_control.html', folder=folder, friends=friends, shared_users={})


@photo_bp.route('/folder/<int:folder_id>/access', methods=['GET', 'POST'])
@login_required
def access_control(folder_id):
    folder = Folder.query.get(folder_id)

    if not folder or folder.user_id != current_user.id:
        flash("Ви не маєте прав керувати доступом.", "danger")
        return redirect(url_for('photo.gallery'))

    shared_access = FolderAccess.query.filter_by(folder_id=folder.id).all()
    shared_users = {User.query.get(acc.user_id): acc.access_level for acc in shared_access}

    friends = User.query.join(Friend, (Friend.friend_id == User.id) & (Friend.user_id == current_user.id))\
        .filter(Friend.status == 'accepted').all()

    form = AddUserForm()
    form.friend_id.choices = [(friend.id, friend.username) for friend in friends]

    if form.validate_on_submit():
        friend_id = form.friend_id.data
        access_level = form.access_level.data
        friend = User.query.get(friend_id)

        existing_access = FolderAccess.query.filter_by(folder_id=folder.id, user_id=friend.id).first()
        if not existing_access:
            new_access = FolderAccess(folder_id=folder.id, user_id=friend.id, access_level=access_level)
            app.db.session.add(new_access)
            app.db.session.commit()
            flash(f"Користувач {friend.username} доданий з рівнем доступу: {access_level}.", "success")
        else:
            existing_access.access_level = access_level
            app.db.session.commit()
            flash("Рівень доступу оновлено.", "info")

        return redirect(url_for('photo.access_control', folder_id=folder.id))

    return render_template('access_control.html', folder=folder, shared_users=shared_users, friends=friends, form=form)


@photo_bp.route('/folder/<int:folder_id>/add_user', methods=['POST'])
@login_required
def add_user_to_folder(folder_id):
    folder = Folder.query.get(folder_id)

    if not folder or folder.user_id != current_user.id:
        flash("Ви не маєте прав додавати користувачів до цієї папки.", "danger")
        return redirect(url_for('photo.gallery'))

    friend_id = request.form['friend_id']
    access_level = request.form['access_level']
    friend = User.query.get(friend_id)

    if friend:
        existing_access = FolderAccess.query.filter_by(folder_id=folder.id, user_id=friend.id).first()
        if not existing_access:
            new_access = FolderAccess(folder_id=folder.id, user_id=friend.id, access_level=access_level)
            app.db.session.add(new_access)
            app.db.session.commit()
            flash(f"Користувач {friend.username} успішно доданий з рівнем доступу: {access_level}.", "success")
        else:
            existing_access.access_level = access_level
            app.db.session.commit()
            flash("Рівень доступу користувача оновлено.", "info")
    else:
        flash("Користувача не знайдено.", "danger")

    return redirect(url_for('photo.access_control', folder_id=folder.id))


@photo_bp.route('/folder/<int:folder_id>/change_access/<int:user_id>', methods=['POST'])
@login_required
def change_access_level(folder_id, user_id):
    folder = Folder.query.get(folder_id)

    if not folder or folder.user_id != current_user.id:
        flash("Ви не маєте прав змінювати доступ для цього користувача.", "danger")
        return redirect(url_for('photo.gallery'))

    new_access_level = request.form['new_access_level']
    user = User.query.get(user_id)

    if user:
        access_record = FolderAccess.query.filter_by(folder_id=folder.id, user_id=user.id).first()
        if access_record:
            access_record.access_level = new_access_level
            app.db.session.commit()
            flash(f"Рівень доступу для {user.username} змінено на: {new_access_level}.", "success")
        else:
            flash("Цей користувач не має доступу до цієї папки.", "danger")
    else:
        flash("Користувача не знайдено.", "danger")

    return redirect(url_for('photo.access_control', folder_id=folder.id))


@photo_bp.route('/folder/<int:folder_id>/remove_user/<int:user_id>', methods=['POST'])
@login_required
def remove_user_from_folder(folder_id, user_id):
    folder = Folder.query.get(folder_id)

    if not folder or folder.user_id != current_user.id:
        flash("Ви не маєте прав змінювати доступ.", "danger")
        return redirect(url_for('photo.gallery'))

    access = FolderAccess.query.filter_by(folder_id=folder.id, user_id=user_id).first()

    if access:
        if user_id in [user.id for user in folder.shared_with]:
            folder.shared_with = [user for user in folder.shared_with if user.id != user_id]

        app.db.session.delete(access)
        app.db.session.commit()
        flash("Користувач видалений з доступу.", "success")
    else:
        flash("Користувач не має доступу до цієї папки.", "warning")

    return redirect(url_for('photo.access_control', folder_id=folder.id))