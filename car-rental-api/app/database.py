from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = "sqlite:///./car_rental.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_database() -> None:
    """SQLite-safe migrations for already existing local databases."""
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    if "vehicles" in tables:
        vehicle_columns = {c["name"] for c in inspector.get_columns("vehicles")}
        with engine.begin() as connection:
            if "image_url" not in vehicle_columns:
                connection.execute(
                    text("ALTER TABLE vehicles ADD COLUMN image_url VARCHAR(1000)")
                )
            if "specs" not in vehicle_columns:
                connection.execute(
                    text("ALTER TABLE vehicles ADD COLUMN specs JSON")
                )

    if "users" in tables:
        user_columns = {c["name"] for c in inspector.get_columns("users")}
        with engine.begin() as connection:
            if "password_hash" not in user_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"))
            if "role" not in user_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'CUSTOMER'"))

    if "bookings" in tables:
        booking_columns = {c["name"] for c in inspector.get_columns("bookings")}
        with engine.begin() as connection:
            if "vehicle_origin_location_id" not in booking_columns:
                connection.execute(text("ALTER TABLE bookings ADD COLUMN vehicle_origin_location_id INTEGER NOT NULL DEFAULT 1"))
            if "rental_price" not in booking_columns:
                connection.execute(text("ALTER TABLE bookings ADD COLUMN rental_price NUMERIC(10, 2) NOT NULL DEFAULT 0"))
            if "transfer_fee" not in booking_columns:
                connection.execute(text("ALTER TABLE bookings ADD COLUMN transfer_fee NUMERIC(10, 2) NOT NULL DEFAULT 0"))
