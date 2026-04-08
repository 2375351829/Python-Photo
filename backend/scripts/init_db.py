import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal, engine, Base
from backend.app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_tables():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


def create_default_admin(db: Session):
    admin_user = db.query(User).filter(User.username == "admin").first()
    
    if admin_user:
        print("Default admin user already exists.")
        return
    
    admin_user = User(
        username="admin",
        email="admin@example.com",
        password_hash=pwd_context.hash("admin123"),
        role="admin",
        is_active=True,
    )
    
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    print(f"Default admin user created successfully!")
    print(f"Username: admin")
    print(f"Password: admin123")
    print(f"Email: admin@example.com")


def init_database():
    print("=" * 50)
    print("Initializing database...")
    print("=" * 50)
    
    create_tables()
    
    db = SessionLocal()
    try:
        create_default_admin(db)
    finally:
        db.close()
    
    print("=" * 50)
    print("Database initialization completed!")
    print("=" * 50)


if __name__ == "__main__":
    init_database()
