from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import hash_password

def create_user(name, email, password, role):
    db = SessionLocal()

    user = User(
        name=name,
        email=email,
        password=hash_password(password),
        role=role
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    db.close()
    return user