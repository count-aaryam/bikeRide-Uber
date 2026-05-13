from app.db.session import engine, Base
from app.models.user import User

Base.metadata.create_all(bind=engine)

print("Tables created")