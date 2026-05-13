from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import verify_password

def authenticate_user(email: str, password: str):
    db = SessionLocal()

    user = db.query(User).filter(User.email == email).first()

    db.close()

    if not user:
        return None

    if not verify_password(password, user.password):
        return None

    return user