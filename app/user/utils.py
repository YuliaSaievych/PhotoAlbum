from app.models import User


def load_user(user_id):
    user = User.query.get(int(user_id))
    if not user:
        print(f"Користувач {user_id} не знайдений")
    return user