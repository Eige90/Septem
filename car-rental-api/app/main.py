from contextlib import asynccontextmanager
from datetime import UTC, date, datetime
from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import and_, exists, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import models, schemas, services
from .database import Base, SessionLocal, engine, get_db, migrate_database
from .seed import seed_database
from .security import (
    create_session,
    delete_current_session,
    get_bearer_token,
    get_current_user,
    get_current_admin,
    hash_password,
    verify_password,
)


API_VERSION = "3.3.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    migrate_database()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
        services.sync_vehicle_current_locations(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="SEPTUM Rental Management API",
    version=API_VERSION,
    description=(
        "Internal management API for the SEPTUM rental operator. "
        "The regular /users, /bookings and /invoices endpoints are admin/management CRUD endpoints. "
        "End-consumer authentication and self-service use /auth and /customer endpoints instead."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# HELPERS
# ============================================================

def get_or_404(db: Session, model, object_id: int, label: str):
    obj = db.get(model, object_id)
    if obj is None:
        raise HTTPException(status_code=404, detail=f"{label} not found")
    return obj


def validate_location(db: Session, location_id: int) -> models.Location:
    location = get_or_404(db, models.Location, location_id, "Location")
    if not location.active:
        raise HTTPException(status_code=409, detail="Location is inactive")
    return location


def validate_user(db: Session, user_id: int) -> models.User:
    user = get_or_404(db, models.User, user_id, "User")
    if not user.active:
        raise HTTPException(status_code=409, detail="User is inactive")
    return user


def validate_vehicle(db: Session, vehicle_id: int) -> models.Vehicle:
    vehicle = get_or_404(db, models.Vehicle, vehicle_id, "Vehicle")
    if not vehicle.active:
        raise HTTPException(status_code=409, detail="Vehicle is inactive")
    return vehicle


def recalculate_booking(
    db: Session,
    booking: models.Booking,
    vehicle: models.Vehicle,
) -> None:
    if booking.end_date <= booking.start_date:
        raise HTTPException(status_code=422, detail="end_date must be later than start_date")
    services.apply_booking_price(db, booking, vehicle, exclude_booking_id=booking.id)


def ensure_no_conflict(
    db: Session,
    booking: models.Booking,
    exclude_booking_id: int | None = None,
):
    if booking.status != "CONFIRMED":
        return

    conflict = services.find_booking_conflict(
        db,
        booking.vehicle_id,
        booking.start_date,
        booking.end_date,
        exclude_booking_id=exclude_booking_id,
    )

    if conflict is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Vehicle is already booked for this period",
                "conflicting_booking_id": conflict.id,
                "conflicting_start_date": str(conflict.start_date),
                "conflicting_end_date": str(conflict.end_date),
            },
        )




def require_same_user(requested_user_id: int, current_user: models.User) -> None:
    if requested_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only access your own account")


def get_owned_booking(db: Session, booking_id: int, current_user: models.User) -> models.Booking:
    booking = get_or_404(db, models.Booking, booking_id, "Booking")
    if booking.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


def get_owned_invoice(db: Session, invoice_id: int, current_user: models.User) -> models.Invoice:
    invoice = get_or_404(db, models.Invoice, invoice_id, "Invoice")
    if invoice.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


# ============================================================
# SYSTEM
# ============================================================

@app.get(
    "/",
    tags=["System"],
    summary="API information",
    description="Basic information and useful links for the SEPTUM Rental API.",
)
def root():
    return {
        "name": "SEPTUM Rental Management API",
        "status": "online",
        "version": API_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "health": "/health",
    }


@app.get(
    "/health",
    tags=["System"],
    summary="Health check",
)
def health():
    return {
        "status": "ok",
        "version": API_VERSION,
    }


# ============================================================
# ADMIN AUTH - OPERATOR / MANAGEMENT
# ============================================================

@app.post("/admin/login", response_model=schemas.AuthRead, tags=["Admin Auth"])
def admin_login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    email = str(payload.email).strip().lower()
    user = db.scalar(select(models.User).where(models.User.email == email))
    if user is None or user.role != "ADMIN" or not user.active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid administrator credentials")
    token = create_session(db, user)
    return schemas.AuthRead(access_token=token, user=user)


@app.get("/admin/me", response_model=schemas.UserRead, tags=["Admin Auth"])
def admin_me(current_admin: models.User = Depends(get_current_admin)):
    return current_admin


# ============================================================
# CUSTOMER AUTH - END-CONSUMER LOGIN / REGISTRATION
# ============================================================

@app.post("/auth/register", response_model=schemas.AuthRead, status_code=201, tags=["Customer Auth"])
def register(payload: schemas.RegisterRequest, db: Session = Depends(get_db)):
    email = str(payload.email).strip().lower()
    if db.scalar(select(models.User).where(models.User.email == email)) is not None:
        raise HTTPException(status_code=409, detail="Email already exists")

    user = models.User(
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        email=email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role="CUSTOMER",
        active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_session(db, user)
    return schemas.AuthRead(access_token=token, user=user)


@app.post("/auth/login", response_model=schemas.AuthRead, tags=["Customer Auth"])
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    email = str(payload.email).strip().lower()
    user = db.scalar(select(models.User).where(models.User.email == email))
    if user is None or user.role != "CUSTOMER" or not user.active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_session(db, user)
    return schemas.AuthRead(access_token=token, user=user)


@app.get("/auth/me", response_model=schemas.UserRead, tags=["Customer Auth"])
def me(current_user: models.User = Depends(get_current_user)):
    return current_user


@app.post("/auth/logout", status_code=204, tags=["Customer Auth"])
def logout(
    raw_token: str = Depends(get_bearer_token),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    del current_user
    delete_current_session(raw_token, db)
    return Response(status_code=204)


# ============================================================
# USERS - INTERNAL / ADMIN CRUD
# ============================================================

@app.post("/users", response_model=schemas.UserRead, status_code=201, tags=["Users"], dependencies=[Depends(get_current_admin)])
def create_user(payload: schemas.AdminUserCreate, db: Session = Depends(get_db)):
    email = str(payload.email).strip().lower()
    if db.scalar(select(models.User).where(models.User.email == email)) is not None:
        raise HTTPException(status_code=409, detail="Email already exists")

    user = models.User(
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        email=email,
        phone=payload.phone,
        password_hash=hash_password(payload.password) if payload.password else None,
        role="CUSTOMER",
        active=payload.active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/users", response_model=list[schemas.UserRead], tags=["Users"], dependencies=[Depends(get_current_admin)])
def list_users(
    active: bool | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(models.User)

    if active is not None:
        stmt = stmt.where(models.User.active == active)

    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                models.User.first_name.ilike(term),
                models.User.last_name.ilike(term),
                models.User.email.ilike(term),
            )
        )

    return list(db.scalars(stmt.order_by(models.User.id.asc())).all())


@app.get("/users/{user_id}", response_model=schemas.UserRead, tags=["Users"], dependencies=[Depends(get_current_admin)])
def get_user(user_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, models.User, user_id, "User")


@app.put("/users/{user_id}", response_model=schemas.UserRead, tags=["Users"], dependencies=[Depends(get_current_admin)])
def replace_user(
    user_id: int,
    payload: schemas.AdminUserPut,
    db: Session = Depends(get_db),
):
    user = get_or_404(db, models.User, user_id, "User")
    user.first_name = payload.first_name.strip()
    user.last_name = payload.last_name.strip()
    user.email = str(payload.email).strip().lower()
    user.phone = payload.phone
    user.active = payload.active
    if payload.password:
        user.password_hash = hash_password(payload.password)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already exists")

    db.refresh(user)
    return user


@app.patch("/users/{user_id}", response_model=schemas.UserRead, tags=["Users"], dependencies=[Depends(get_current_admin)])
def patch_user(
    user_id: int,
    payload: schemas.AdminUserPatch,
    db: Session = Depends(get_db),
):
    user = get_or_404(db, models.User, user_id, "User")
    data = payload.model_dump(exclude_unset=True)
    password = data.pop("password", None)

    for field, value in data.items():
        if field == "email" and value is not None:
            value = str(value).strip().lower()
        setattr(user, field, value)

    if password:
        user.password_hash = hash_password(password)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already exists")

    db.refresh(user)
    return user


@app.delete("/users/{user_id}", status_code=204, tags=["Users"], dependencies=[Depends(get_current_admin)])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = get_or_404(db, models.User, user_id, "User")
    user.active = False
    db.commit()
    return Response(status_code=204)


# ============================================================
# LOCATIONS - GET / POST / PUT / PATCH / DELETE
# ============================================================

@app.post(
    "/locations",
    response_model=schemas.LocationRead,
    status_code=201,
    tags=["Locations"],
    dependencies=[Depends(get_current_admin)],
)
def create_location(
    payload: schemas.LocationCreate,
    db: Session = Depends(get_db),
):
    location = models.Location(**payload.model_dump())
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


@app.get(
    "/locations",
    response_model=list[schemas.LocationRead],
    tags=["Locations"],
    dependencies=[Depends(get_current_admin)],
)
def list_locations(
    city: str | None = None,
    country: str | None = None,
    active: bool | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(models.Location)

    if city:
        stmt = stmt.where(models.Location.city.ilike(f"%{city}%"))
    if country:
        stmt = stmt.where(models.Location.country.ilike(f"%{country}%"))
    if active is not None:
        stmt = stmt.where(models.Location.active == active)

    return list(db.scalars(stmt.order_by(models.Location.id.asc())).all())


@app.get(
    "/locations/{location_id}",
    response_model=schemas.LocationRead,
    tags=["Locations"],
    dependencies=[Depends(get_current_admin)],
)
def get_location(location_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, models.Location, location_id, "Location")


@app.put(
    "/locations/{location_id}",
    response_model=schemas.LocationRead,
    tags=["Locations"],
    dependencies=[Depends(get_current_admin)],
)
def replace_location(
    location_id: int,
    payload: schemas.LocationPut,
    db: Session = Depends(get_db),
):
    location = get_or_404(db, models.Location, location_id, "Location")

    for field, value in payload.model_dump().items():
        setattr(location, field, value)

    db.commit()
    db.refresh(location)
    return location


@app.patch(
    "/locations/{location_id}",
    response_model=schemas.LocationRead,
    tags=["Locations"],
    dependencies=[Depends(get_current_admin)],
)
def patch_location(
    location_id: int,
    payload: schemas.LocationPatch,
    db: Session = Depends(get_db),
):
    location = get_or_404(db, models.Location, location_id, "Location")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(location, field, value)

    db.commit()
    db.refresh(location)
    return location


@app.delete("/locations/{location_id}", status_code=204, tags=["Locations"], dependencies=[Depends(get_current_admin)])
def delete_location(location_id: int, db: Session = Depends(get_db)):
    location = get_or_404(db, models.Location, location_id, "Location")

    vehicle_exists = db.scalar(
        select(exists().where(models.Vehicle.location_id == location_id))
    )
    booking_exists = db.scalar(
        select(
            exists().where(
                or_(
                    models.Booking.pickup_location_id == location_id,
                    models.Booking.dropoff_location_id == location_id,
                )
            )
        )
    )

    if vehicle_exists or booking_exists:
        raise HTTPException(
            status_code=409,
            detail="Location cannot be deleted because it is in use",
        )

    db.delete(location)
    db.commit()
    return Response(status_code=204)


# ============================================================
# VEHICLES - GET / POST / PUT / PATCH / DELETE
# ============================================================

@app.post(
    "/vehicles",
    response_model=schemas.VehicleRead,
    status_code=201,
    tags=["Vehicles"],
    dependencies=[Depends(get_current_admin)],
)
def create_vehicle(
    payload: schemas.VehicleCreate,
    db: Session = Depends(get_db),
):
    validate_location(db, payload.location_id)

    vehicle = models.Vehicle(**payload.model_dump())
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


@app.get(
    "/vehicles",
    response_model=list[schemas.VehicleRead],
    tags=["Vehicles"],
    dependencies=[Depends(get_current_admin)],
)
def list_vehicles(
    brand: str | None = Query(default=None, min_length=1),
    model: str | None = Query(default=None, min_length=1),
    vehicle_type: schemas.VehicleType | None = None,
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    location_id: int | None = None,
    is_real_world: bool | None = None,
    available_from: date | None = None,
    available_to: date | None = None,
    active: bool | None = True,
    db: Session = Depends(get_db),
):
    if (available_from is None) != (available_to is None):
        raise HTTPException(
            status_code=422,
            detail="available_from and available_to must be supplied together",
        )

    if available_from and available_to and available_to <= available_from:
        raise HTTPException(
            status_code=422,
            detail="available_to must be later than available_from",
        )

    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=422,
            detail="min_price cannot be greater than max_price",
        )

    stmt = select(models.Vehicle)

    if active is not None:
        stmt = stmt.where(models.Vehicle.active == active)

    if brand is not None:
        stmt = stmt.where(
            models.Vehicle.brand.ilike(f"%{brand.strip()}%")
        )

    if model is not None:
        stmt = stmt.where(
            models.Vehicle.model.ilike(f"%{model.strip()}%")
        )

    if vehicle_type is not None:
        stmt = stmt.where(models.Vehicle.vehicle_type == vehicle_type.value)

    if min_price is not None:
        stmt = stmt.where(models.Vehicle.daily_rate >= min_price)

    if max_price is not None:
        stmt = stmt.where(models.Vehicle.daily_rate <= max_price)

    if location_id is not None:
        stmt = stmt.where(models.Vehicle.location_id == location_id)

    if is_real_world is not None:
        stmt = stmt.where(models.Vehicle.is_real_world == is_real_world)

    if available_from is not None and available_to is not None:
        overlapping_booking = exists().where(
            and_(
                models.Booking.vehicle_id == models.Vehicle.id,
                services.booking_overlap_condition(
                    available_from,
                    available_to,
                ),
            )
        )
        stmt = stmt.where(~overlapping_booking)

    stmt = stmt.order_by(models.Vehicle.id.asc())

    return list(db.scalars(stmt).all())


@app.get(
    "/vehicles/{vehicle_id}",
    response_model=schemas.VehicleRead,
    tags=["Vehicles"],
    dependencies=[Depends(get_current_admin)],
)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, models.Vehicle, vehicle_id, "Vehicle")


@app.get(
    "/vehicles/{vehicle_id}/availability",
    response_model=schemas.AvailabilityRead,
    tags=["Vehicles"],
    dependencies=[Depends(get_current_admin)],
)
def check_vehicle_availability(
    vehicle_id: int,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
):
    if end_date <= start_date:
        raise HTTPException(
            status_code=422,
            detail="end_date must be later than start_date",
        )

    vehicle = validate_vehicle(db, vehicle_id)
    available = services.vehicle_is_available(
        db,
        vehicle_id,
        start_date,
        end_date,
    )

    return schemas.AvailabilityRead(
        vehicle_id=vehicle.id,
        available=available,
        start_date=start_date,
        end_date=end_date,
        rental_days=services.rental_days(start_date, end_date),
        daily_rate=vehicle.daily_rate,
        total_price=services.calculate_total_price(
            vehicle.daily_rate,
            start_date,
            end_date,
        ),
    )


@app.put(
    "/vehicles/{vehicle_id}",
    response_model=schemas.VehicleRead,
    tags=["Vehicles"],
    dependencies=[Depends(get_current_admin)],
)
def replace_vehicle(
    vehicle_id: int,
    payload: schemas.VehiclePut,
    db: Session = Depends(get_db),
):
    vehicle = get_or_404(db, models.Vehicle, vehicle_id, "Vehicle")
    validate_location(db, payload.location_id)

    for field, value in payload.model_dump().items():
        setattr(vehicle, field, value)

    db.commit()
    db.refresh(vehicle)
    return vehicle


@app.patch(
    "/vehicles/{vehicle_id}",
    response_model=schemas.VehicleRead,
    tags=["Vehicles"],
    dependencies=[Depends(get_current_admin)],
)
def patch_vehicle(
    vehicle_id: int,
    payload: schemas.VehiclePatch,
    db: Session = Depends(get_db),
):
    vehicle = get_or_404(db, models.Vehicle, vehicle_id, "Vehicle")
    data = payload.model_dump(exclude_unset=True)

    if "location_id" in data and data["location_id"] is not None:
        validate_location(db, data["location_id"])

    for field, value in data.items():
        setattr(vehicle, field, value)

    db.commit()
    db.refresh(vehicle)
    return vehicle


@app.delete("/vehicles/{vehicle_id}", status_code=204, tags=["Vehicles"], dependencies=[Depends(get_current_admin)])
def delete_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    vehicle = get_or_404(db, models.Vehicle, vehicle_id, "Vehicle")

    booking_exists = db.scalar(
        select(exists().where(models.Booking.vehicle_id == vehicle_id))
    )
    if booking_exists:
        raise HTTPException(
            status_code=409,
            detail="Vehicle cannot be deleted because bookings exist",
        )

    db.delete(vehicle)
    db.commit()
    return Response(status_code=204)




# ============================================================
# PUBLIC CATALOG - END-CONSUMER READ ONLY
# ============================================================

@app.get("/catalog/locations", response_model=list[schemas.LocationRead], tags=["Public Catalog"])
def catalog_locations(
    city: str | None = None,
    country: str | None = None,
    active: bool | None = True,
    db: Session = Depends(get_db),
):
    services.sync_vehicle_current_locations(db)
    stmt = select(models.Location)
    if city:
        stmt = stmt.where(models.Location.city.ilike(f"%{city.strip()}%"))
    if country:
        stmt = stmt.where(models.Location.country.ilike(f"%{country.strip()}%"))
    if active is not None:
        stmt = stmt.where(models.Location.active == active)
    return list(db.scalars(stmt.order_by(models.Location.id.asc())).all())


@app.get("/catalog/vehicles", response_model=list[schemas.VehicleRead], tags=["Public Catalog"])
def catalog_vehicles(
    brand: str | None = None,
    model: str | None = None,
    vehicle_type: schemas.VehicleType | None = None,
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    location_id: int | None = None,
    is_real_world: bool | None = None,
    available_from: date | None = None,
    available_to: date | None = None,
    active: bool | None = True,
    db: Session = Depends(get_db),
):
    services.sync_vehicle_current_locations(db)
    stmt = select(models.Vehicle)
    if brand:
        stmt = stmt.where(models.Vehicle.brand.ilike(f"%{brand.strip()}%"))
    if model:
        stmt = stmt.where(models.Vehicle.model.ilike(f"%{model.strip()}%"))
    if vehicle_type:
        stmt = stmt.where(models.Vehicle.vehicle_type == vehicle_type.value)
    if min_price is not None:
        stmt = stmt.where(models.Vehicle.daily_rate >= min_price)
    if max_price is not None:
        stmt = stmt.where(models.Vehicle.daily_rate <= max_price)
    if location_id is not None:
        stmt = stmt.where(models.Vehicle.location_id == location_id)
    if is_real_world is not None:
        stmt = stmt.where(models.Vehicle.is_real_world == is_real_world)
    if active is not None:
        stmt = stmt.where(models.Vehicle.active == active)
    vehicles = list(db.scalars(stmt.order_by(models.Vehicle.id.asc())).all())
    if available_from is not None or available_to is not None:
        if available_from is None or available_to is None or available_to <= available_from:
            raise HTTPException(status_code=422, detail="Both valid availability dates are required")
        vehicles = [v for v in vehicles if services.vehicle_is_available(db, v.id, available_from, available_to)]
    return vehicles


@app.get("/catalog/vehicles/{vehicle_id}", response_model=schemas.VehicleRead, tags=["Public Catalog"])
def catalog_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    services.sync_vehicle_current_locations(db)
    vehicle = validate_vehicle(db, vehicle_id)
    return vehicle


# ============================================================
# BOOKINGS - INTERNAL / ADMIN CRUD
# ============================================================

@app.post("/bookings", response_model=schemas.BookingRead, status_code=201, tags=["Bookings"], dependencies=[Depends(get_current_admin)])
def create_booking(
    payload: schemas.AdminBookingCreate,
    db: Session = Depends(get_db),
):
    user = validate_user(db, payload.user_id)
    vehicle = validate_vehicle(db, payload.vehicle_id)
    validate_location(db, payload.pickup_location_id)
    validate_location(db, payload.dropoff_location_id)

    data = payload.model_dump()
    booking = models.Booking(
        **data,
        rental_days=services.rental_days(payload.start_date, payload.end_date),
        vehicle_origin_location_id=vehicle.location_id,
        rental_price=Decimal("0.00"),
        transfer_fee=Decimal("0.00"),
        total_price=Decimal("0.00"),
    )
    del user
    ensure_no_conflict(db, booking)
    services.apply_booking_price(db, booking, vehicle)
    db.add(booking)
    db.commit()
    db.refresh(booking)
    services.recalculate_future_booking_prices(db, vehicle.id, booking.start_date)
    services.sync_vehicle_current_locations(db)
    db.refresh(booking)
    return booking


@app.get("/bookings", response_model=list[schemas.BookingRead], tags=["Bookings"], dependencies=[Depends(get_current_admin)])
def list_bookings(
    user_id: int | None = None,
    vehicle_id: int | None = None,
    booking_status: schemas.BookingStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    stmt = select(models.Booking)
    if user_id is not None:
        stmt = stmt.where(models.Booking.user_id == user_id)
    if vehicle_id is not None:
        stmt = stmt.where(models.Booking.vehicle_id == vehicle_id)
    if booking_status is not None:
        stmt = stmt.where(models.Booking.status == booking_status.value)
    return list(db.scalars(stmt.order_by(models.Booking.id.asc())).all())


@app.get("/bookings/{booking_id}", response_model=schemas.BookingRead, tags=["Bookings"], dependencies=[Depends(get_current_admin)])
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, models.Booking, booking_id, "Booking")


@app.put("/bookings/{booking_id}", response_model=schemas.BookingRead, tags=["Bookings"], dependencies=[Depends(get_current_admin)])
def replace_booking(
    booking_id: int,
    payload: schemas.AdminBookingPut,
    db: Session = Depends(get_db),
):
    booking = get_or_404(db, models.Booking, booking_id, "Booking")
    validate_user(db, payload.user_id)
    vehicle = validate_vehicle(db, payload.vehicle_id)
    validate_location(db, payload.pickup_location_id)
    validate_location(db, payload.dropoff_location_id)

    for field, value in payload.model_dump().items():
        setattr(booking, field, value)

    recalculate_booking(db, booking, vehicle)
    ensure_no_conflict(db, booking, exclude_booking_id=booking.id)
    db.commit()
    db.refresh(booking)
    services.recalculate_future_booking_prices(db, booking.vehicle_id, booking.start_date)
    services.sync_vehicle_current_locations(db)
    db.refresh(booking)
    return booking


@app.patch("/bookings/{booking_id}", response_model=schemas.BookingRead, tags=["Bookings"], dependencies=[Depends(get_current_admin)])
def patch_booking(
    booking_id: int,
    payload: schemas.AdminBookingPatch,
    db: Session = Depends(get_db),
):
    booking = get_or_404(db, models.Booking, booking_id, "Booking")
    data = payload.model_dump(exclude_unset=True)

    if "user_id" in data and data["user_id"] is not None:
        validate_user(db, data["user_id"])
    if "vehicle_id" in data and data["vehicle_id"] is not None:
        validate_vehicle(db, data["vehicle_id"])
    if "pickup_location_id" in data and data["pickup_location_id"] is not None:
        validate_location(db, data["pickup_location_id"])
    if "dropoff_location_id" in data and data["dropoff_location_id"] is not None:
        validate_location(db, data["dropoff_location_id"])

    for field, value in data.items():
        setattr(booking, field, value)

    vehicle = validate_vehicle(db, booking.vehicle_id)
    recalculate_booking(db, booking, vehicle)
    ensure_no_conflict(db, booking, exclude_booking_id=booking.id)
    db.commit()
    db.refresh(booking)
    services.recalculate_future_booking_prices(db, booking.vehicle_id, booking.start_date)
    services.sync_vehicle_current_locations(db)
    db.refresh(booking)
    return booking


@app.delete("/bookings/{booking_id}", status_code=204, tags=["Bookings"], dependencies=[Depends(get_current_admin)])
def delete_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = get_or_404(db, models.Booking, booking_id, "Booking")
    vehicle_id = booking.vehicle_id
    start_date = booking.start_date
    db.delete(booking)
    db.commit()
    services.recalculate_future_booking_prices(db, vehicle_id, start_date)
    services.sync_vehicle_current_locations(db)
    return Response(status_code=204)


# ============================================================
# CUSTOMER BOOKINGS - END-CONSUMER SELF SERVICE
# ============================================================

@app.post(
    "/customer/bookings/quote",
    response_model=schemas.BookingQuoteRead,
    tags=["Customer Self-Service"],
    summary="Preview booking price",
    description=(
        "Read-only price preview. The customer only submits vehicle, locations and dates. "
        "Rental price, transfer fee and total are always calculated by the server. "
        "Changing the selection requires a new quote."
    ),
)
def customer_booking_quote(
    payload: schemas.CustomerBookingRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    del current_user
    vehicle = validate_vehicle(db, payload.vehicle_id)
    validate_location(db, payload.pickup_location_id)
    validate_location(db, payload.dropoff_location_id)
    if not services.vehicle_is_available(db, vehicle.id, payload.start_date, payload.end_date):
        raise HTTPException(status_code=409, detail="Vehicle is already booked for this period")
    origin, rental_price, transfer_fee, total = services.booking_price_breakdown(
        db, vehicle, payload.pickup_location_id, payload.start_date, payload.end_date
    )
    return schemas.BookingQuoteRead(
        vehicle_id=vehicle.id,
        vehicle_origin_location_id=origin,
        pickup_location_id=payload.pickup_location_id,
        dropoff_location_id=payload.dropoff_location_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        rental_days=services.rental_days(payload.start_date, payload.end_date),
        daily_rate=vehicle.daily_rate,
        rental_price=rental_price,
        transfer_fee=transfer_fee,
        total_price=total,
        quote_generated_at=datetime.now(UTC),
    )


@app.post(
    "/customer/bookings",
    response_model=schemas.CustomerBookingRead,
    status_code=201,
    tags=["Customer Self-Service"],
    summary="Create booking with server-side final price check",
    description=(
        "Creates the booking from customer-controlled inputs only. Availability, effective vehicle "
        "location, transfer fee and final total are recalculated again by the server at booking time; "
        "a previously displayed quote is never trusted as the final price."
    ),
)
def customer_create_booking(
    payload: schemas.CustomerBookingRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    vehicle = validate_vehicle(db, payload.vehicle_id)
    validate_location(db, payload.pickup_location_id)
    validate_location(db, payload.dropoff_location_id)

    booking = models.Booking(
        user_id=current_user.id,
        **payload.model_dump(),
        status="CONFIRMED",
        rental_days=services.rental_days(payload.start_date, payload.end_date),
        vehicle_origin_location_id=vehicle.location_id,
        rental_price=Decimal("0.00"),
        transfer_fee=Decimal("0.00"),
        total_price=Decimal("0.00"),
    )
    ensure_no_conflict(db, booking)
    services.apply_booking_price(db, booking, vehicle)
    db.add(booking)
    db.commit()
    db.refresh(booking)
    services.recalculate_future_booking_prices(db, vehicle.id, booking.start_date)
    services.sync_vehicle_current_locations(db)
    db.refresh(booking)
    return booking


@app.get(
    "/customer/bookings",
    response_model=list[schemas.CustomerBookingRead],
    tags=["Customer Self-Service"],
)
def customer_list_bookings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    stmt = (
        select(models.Booking)
        .where(models.Booking.user_id == current_user.id)
        .order_by(models.Booking.id.asc())
    )
    return list(db.scalars(stmt).all())


@app.get(
    "/customer/bookings/{booking_id}",
    response_model=schemas.CustomerBookingRead,
    tags=["Customer Self-Service"],
)
def customer_get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return get_owned_booking(db, booking_id, current_user)


@app.patch(
    "/customer/bookings/{booking_id}",
    response_model=schemas.CustomerBookingRead,
    tags=["Customer Self-Service"],
)
def customer_patch_booking(
    booking_id: int,
    payload: schemas.CustomerBookingPatch,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    booking = get_owned_booking(db, booking_id, current_user)
    data = payload.model_dump(exclude_unset=True)

    if "vehicle_id" in data and data["vehicle_id"] is not None:
        validate_vehicle(db, data["vehicle_id"])
    if "pickup_location_id" in data and data["pickup_location_id"] is not None:
        validate_location(db, data["pickup_location_id"])
    if "dropoff_location_id" in data and data["dropoff_location_id"] is not None:
        validate_location(db, data["dropoff_location_id"])

    for field, value in data.items():
        setattr(booking, field, value)

    booking.user_id = current_user.id
    vehicle = validate_vehicle(db, booking.vehicle_id)
    recalculate_booking(db, booking, vehicle)
    ensure_no_conflict(db, booking, exclude_booking_id=booking.id)
    db.commit()
    db.refresh(booking)
    services.recalculate_future_booking_prices(db, booking.vehicle_id, booking.start_date)
    services.sync_vehicle_current_locations(db)
    db.refresh(booking)
    return booking


@app.delete(
    "/customer/bookings/{booking_id}",
    status_code=204,
    tags=["Customer Self-Service"],
)
def customer_delete_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    booking = get_owned_booking(db, booking_id, current_user)
    vehicle_id = booking.vehicle_id
    start_date = booking.start_date
    db.delete(booking)
    db.commit()
    services.recalculate_future_booking_prices(db, vehicle_id, start_date)
    services.sync_vehicle_current_locations(db)
    return Response(status_code=204)


# ============================================================
# INVOICES - INTERNAL / ADMIN CRUD
# ============================================================

@app.post("/invoices", response_model=schemas.InvoiceRead, status_code=201, tags=["Invoices"], dependencies=[Depends(get_current_admin)])
def create_invoice(payload: schemas.InvoiceCreate, db: Session = Depends(get_db)):
    booking = get_or_404(db, models.Booking, payload.booking_id, "Booking")
    if booking.invoice is not None:
        raise HTTPException(status_code=409, detail="Invoice already exists for booking")

    tax, total = services.calculate_invoice_values(booking.total_price, payload.tax_rate)
    invoice = models.Invoice(
        booking_id=booking.id,
        user_id=booking.user_id,
        subtotal=booking.total_price,
        tax_rate=payload.tax_rate,
        tax_amount=tax,
        total_amount=total,
        status="OPEN",
        due_date=payload.due_date,
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


@app.get("/invoices", response_model=list[schemas.InvoiceRead], tags=["Invoices"], dependencies=[Depends(get_current_admin)])
def list_invoices(
    user_id: int | None = None,
    invoice_status: schemas.InvoiceStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    stmt = select(models.Invoice)
    if user_id is not None:
        stmt = stmt.where(models.Invoice.user_id == user_id)
    if invoice_status is not None:
        stmt = stmt.where(models.Invoice.status == invoice_status.value)
    return list(db.scalars(stmt.order_by(models.Invoice.id.asc())).all())


@app.get("/invoices/{invoice_id}", response_model=schemas.InvoiceRead, tags=["Invoices"], dependencies=[Depends(get_current_admin)])
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, models.Invoice, invoice_id, "Invoice")


@app.put("/invoices/{invoice_id}", response_model=schemas.InvoiceRead, tags=["Invoices"], dependencies=[Depends(get_current_admin)])
def replace_invoice(
    invoice_id: int,
    payload: schemas.InvoicePut,
    db: Session = Depends(get_db),
):
    invoice = get_or_404(db, models.Invoice, invoice_id, "Invoice")
    booking = get_or_404(db, models.Booking, payload.booking_id, "Booking")
    invoice.booking_id = booking.id
    invoice.user_id = booking.user_id
    invoice.subtotal = booking.total_price
    invoice.tax_rate = payload.tax_rate
    invoice.due_date = payload.due_date
    invoice.status = payload.status.value
    tax, total = services.calculate_invoice_values(invoice.subtotal, invoice.tax_rate)
    invoice.tax_amount = tax
    invoice.total_amount = total
    invoice.paid_at = datetime.now(UTC) if invoice.status == "PAID" else None
    db.commit()
    db.refresh(invoice)
    return invoice


@app.patch("/invoices/{invoice_id}", response_model=schemas.InvoiceRead, tags=["Invoices"], dependencies=[Depends(get_current_admin)])
def patch_invoice(
    invoice_id: int,
    payload: schemas.InvoicePatch,
    db: Session = Depends(get_db),
):
    invoice = get_or_404(db, models.Invoice, invoice_id, "Invoice")
    data = payload.model_dump(exclude_unset=True)

    if "booking_id" in data and data["booking_id"] is not None:
        booking = get_or_404(db, models.Booking, data["booking_id"], "Booking")
        invoice.booking_id = booking.id
        invoice.user_id = booking.user_id
        invoice.subtotal = booking.total_price
    if "tax_rate" in data and data["tax_rate"] is not None:
        invoice.tax_rate = data["tax_rate"]
    if "due_date" in data and data["due_date"] is not None:
        invoice.due_date = data["due_date"]
    if "status" in data and data["status"] is not None:
        invoice.status = data["status"].value
        invoice.paid_at = datetime.now(UTC) if invoice.status == "PAID" else None

    tax, total = services.calculate_invoice_values(invoice.subtotal, invoice.tax_rate)
    invoice.tax_amount = tax
    invoice.total_amount = total
    db.commit()
    db.refresh(invoice)
    return invoice


@app.delete("/invoices/{invoice_id}", status_code=204, tags=["Invoices"], dependencies=[Depends(get_current_admin)])
def delete_invoice(invoice_id: int, db: Session = Depends(get_db)):
    invoice = get_or_404(db, models.Invoice, invoice_id, "Invoice")
    db.delete(invoice)
    db.commit()
    return Response(status_code=204)


# ============================================================
# CUSTOMER INVOICES - READ OWN INVOICES ONLY
# ============================================================

@app.get(
    "/customer/invoices",
    response_model=list[schemas.CustomerInvoiceRead],
    tags=["Customer Self-Service"],
)
def customer_list_invoices(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    stmt = (
        select(models.Invoice)
        .where(models.Invoice.user_id == current_user.id)
        .order_by(models.Invoice.id.asc())
    )
    return list(db.scalars(stmt).all())


@app.get(
    "/customer/invoices/{invoice_id}",
    response_model=schemas.CustomerInvoiceRead,
    tags=["Customer Self-Service"],
)
def customer_get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return get_owned_invoice(db, invoice_id, current_user)

