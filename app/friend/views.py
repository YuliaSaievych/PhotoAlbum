import hashlib

from flask import redirect, url_for, flash
from flask_login import current_user, login_required

import app
from app.friend import friend_bp
from app.models import Friend, User


@friend_bp.route('/invite_friend/<string:token>', methods=['GET'])
@login_required
def invite_friend(token):
    users = User.query.all()

    invited_user = None
    for user in users:
        expected_token = hashlib.md5(f"{user.id}-{user.email}".encode()).hexdigest()
        if expected_token == token:
            invited_user = user
            break

    if not invited_user:
        flash("Невірне посилання!", "danger")
        return redirect(url_for('general.home'))

    if current_user.id == invited_user.id:
        flash("Ви не можете додати себе у друзі!", "danger")
        return redirect(url_for('general.home'))

    existing_request = Friend.query.filter_by(user_id=current_user.id, friend_id=invited_user.id).first()
    if existing_request:
        flash("Запит вже надіслано!", "warning")
    else:
        new_friend = Friend(user_id=current_user.id, friend_id=invited_user.id)
        app.db.session.add(new_friend)
        app.db.session.commit()
        flash("Запит у друзі надіслано!", "success")

    return redirect(url_for('user.account', user_id=invited_user.id))


@friend_bp.route('/accept_friend/<int:friend_id>', methods=['POST'])
@login_required
def accept_friend(friend_id):
    friend_request = Friend.query.filter_by(user_id=friend_id, friend_id=current_user.id, status="pending").first()

    if friend_request:
        friend_request.accept()
        app.db.session.commit()
        flash("Запит у друзі прийнято!", "success")
    else:
        flash("Запит не знайдено!", "danger")

    return redirect(url_for('user.account', user_id=friend_id))


@friend_bp.route('/remove_friend/<int:friend_id>', methods=['POST'])
@login_required
def remove_friend(friend_id):
    friend = Friend.query.filter(
        ((Friend.user_id == current_user.id) & (Friend.friend_id == friend_id)) |
        ((Friend.user_id == friend_id) & (Friend.friend_id == current_user.id))
    ).first()

    if friend:
        friend.delete()
        flash("Друг видалений!", "success")
    else:
        flash("Користувач не є вашим другом!", "danger")

    return redirect(url_for('user.account', user_id=friend_id))


