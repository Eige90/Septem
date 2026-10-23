import argparse
from sqlalchemy import select

from .database import Base, SessionLocal, engine, migrate_database
from .models import User
from .security import hash_password


def main():
    parser = argparse.ArgumentParser(description="Create or update a SEPTUM administrator")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--first-name", default="SEPTUM")
    parser.add_argument("--last-name", default="Admin")
    args = parser.parse_args()

    migrate_database()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        email = args.email.strip().lower()
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(
                first_name=args.first_name,
                last_name=args.last_name,
                email=email,
                phone=None,
                password_hash=hash_password(args.password),
                role="ADMIN",
                active=True,
            )
            db.add(user)
        else:
            user.first_name = args.first_name
            user.last_name = args.last_name
            user.password_hash = hash_password(args.password)
            user.role = "ADMIN"
            user.active = True
        db.commit()
        print(f"Administrator ready: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
