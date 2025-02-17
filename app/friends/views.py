from flask import redirect, url_for, flash
from flask_login import current_user, login_required

import app
from app.friends import friends_bp
from app.models import Friend


@friends_bp.route('/add_friend/<int:user_id>', methods=['POST'])
@login_required
def add_friend(user_id):
    if current_user.id == user_id:
        flash("Ви не можете додати себе у друзі!", "danger")
        return redirect(url_for('main.index'))

    existing_request = Friend.query.filter_by(user_id=current_user.id, friend_id=user_id).first()
    if existing_request:
        flash("Запит вже надіслано!", "warning")
    else:
        new_friend = Friend(user_id=current_user.id, friend_id=user_id)
        app.db.session.add(new_friend)
        app.db.session.commit()
        flash("Запит у друзі надіслано!", "success")

    return redirect(url_for('user.profile', user_id=user_id))


@friends_bp.route('/accept_friend/<int:friend_id>', methods=['POST'])
@login_required
def accept_friend(friend_id):
    friend_request = Friend.query.filter_by(user_id=friend_id, friend_id=current_user.id, status="pending").first()

    if friend_request:
        friend_request.accept()
        flash("Запит у друзі прийнято!", "success")
    else:
        flash("Запит не знайдено!", "danger")

    return redirect(url_for('user.profile', user_id=friend_id))


@friends_bp.route('/remove_friend/<int:friend_id>', methods=['POST'])
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

    return redirect(url_for('user.profile', user_id=friend_id))


