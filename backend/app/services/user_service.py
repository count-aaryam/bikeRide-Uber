from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import hash_password
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

def create_user(name, email, password, role):
    db = SessionLocal()

    try:
        user = User(
            name=name,
            email=email,
            password=hash_password(password),
            role=role
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    finally:
        db.close()