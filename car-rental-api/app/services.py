from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from . import models


def rental_days(start_date: date, end_date: date) -> int:
    return (end_date - start_date).days


def calculate_total_price(
    daily_rate: Decimal,
    start_date: date,
    end_date: date,
) -> Decimal:
    days = rental_days(start_date, end_date)
    return (daily_rate * days).quantize(Decimal("0.01"))


def booking_overlap_condition(
    start_date: date,
    end_date: date,
    exclude_booking_id: int | None = None,
):
    conditions = [
        models.Booking.status == "CONFIRMED",
        models.Booking.start_date < end_date,
        models.Booking.end_date > start_date,
    ]

    if exclude_booking_id is not None:
        conditions.append(models.Booking.id != exclude_booking_id)

    return and_(*conditions)


def find_booking_conflict(
    db: Session,
    vehicle_id: int,
    start_date: date,
    end_date: date,
    exclude_booking_id: int | None = None,
):
    stmt = (
        select(models.Booking)
        .where(
            models.Booking.vehicle_id == vehicle_id,
            booking_overlap_condition(
                start_date,
                end_date,
                exclude_booking_id,
            ),
        )
        .order_by(models.Booking.start_date)
    )
    return db.scalars(stmt).first()


def vehicle_is_available(
    db: Session,
    vehicle_id: int,
    start_date: date,
    end_date: date,
    exclude_booking_id: int | None = None,
) -> bool:
    return (
        find_booking_conflict(
            db,
            vehicle_id,
            start_date,
            end_date,
            exclude_booking_id,
        )
        is None
    )


def calculate_invoice_values(
    subtotal: Decimal,
    tax_rate: Decimal,
) -> tuple[Decimal, Decimal]:
    tax_amount = (
        subtotal * tax_rate / Decimal("100")
    ).quantize(Decimal("0.01"))

    total_amount = (subtotal + tax_amount).quantize(Decimal("0.01"))
    return tax_amount, total_amount


def apply_invoice_status(invoice: models.Invoice, status: str) -> None:
    invoice.status = status
    if status == "PAID" and invoice.paid_at is None:
        invoice.paid_at = datetime.now(UTC)
    elif status != "PAID":
        invoice.paid_at = None


TRANSFER_FEE = Decimal("500.00")


def effective_vehicle_location_id(
    db: Session,
    vehicle_id: int,
    at_date: date,
    exclude_booking_id: int | None = None,
) -> int:
    vehicle = db.get(models.Vehicle, vehicle_id)
    if vehicle is None:
        raise ValueError("Vehicle not found")

    stmt = select(models.Booking).where(
        models.Booking.vehicle_id == vehicle_id,
        models.Booking.status == "CONFIRMED",
        models.Booking.end_date <= at_date,
    )
    if exclude_booking_id is not None:
        stmt = stmt.where(models.Booking.id != exclude_booking_id)
    stmt = stmt.order_by(models.Booking.end_date.desc(), models.Booking.id.desc())
    prior = db.scalars(stmt).first()
    return prior.dropoff_location_id if prior is not None else vehicle.location_id


def booking_price_breakdown(
    db: Session,
    vehicle: models.Vehicle,
    pickup_location_id: int,
    start_date: date,
    end_date: date,
    exclude_booking_id: int | None = None,
) -> tuple[int, Decimal, Decimal, Decimal]:
    origin_location_id = effective_vehicle_location_id(
        db, vehicle.id, start_date, exclude_booking_id=exclude_booking_id
    )
    rental_price = calculate_total_price(vehicle.daily_rate, start_date, end_date)
    transfer_fee = TRANSFER_FEE if pickup_location_id != origin_location_id else Decimal("0.00")
    total_price = (rental_price + transfer_fee).quantize(Decimal("0.01"))
    return origin_location_id, rental_price, transfer_fee, total_price


def apply_booking_price(
    db: Session,
    booking: models.Booking,
    vehicle: models.Vehicle,
    exclude_booking_id: int | None = None,
) -> None:
    origin, rental_price, transfer_fee, total = booking_price_breakdown(
        db, vehicle, booking.pickup_location_id, booking.start_date, booking.end_date,
        exclude_booking_id=exclude_booking_id,
    )
    booking.rental_days = rental_days(booking.start_date, booking.end_date)
    booking.vehicle_origin_location_id = origin
    booking.rental_price = rental_price
    booking.transfer_fee = transfer_fee
    booking.total_price = total


def recalculate_future_booking_prices(
    db: Session,
    vehicle_id: int,
    from_date: date,
) -> None:
    vehicle = db.get(models.Vehicle, vehicle_id)
    if vehicle is None:
        return
    rows = list(db.scalars(
        select(models.Booking).where(
            models.Booking.vehicle_id == vehicle_id,
            models.Booking.start_date >= from_date,
        ).order_by(models.Booking.start_date.asc(), models.Booking.id.asc())
    ).all())
    for booking in rows:
        apply_booking_price(db, booking, vehicle, exclude_booking_id=booking.id)
    db.commit()


def sync_vehicle_current_locations(db: Session, as_of: date | None = None) -> None:
    as_of = as_of or date.today()
    vehicles = list(db.scalars(select(models.Vehicle)).all())
    changed = False
    for vehicle in vehicles:
        stmt = (
            select(models.Booking)
            .where(
                models.Booking.vehicle_id == vehicle.id,
                models.Booking.status == "CONFIRMED",
                models.Booking.end_date <= as_of,
            )
            .order_by(models.Booking.end_date.desc(), models.Booking.id.desc())
        )
        latest = db.scalars(stmt).first()
        if latest is not None and vehicle.location_id != latest.dropoff_location_id:
            vehicle.location_id = latest.dropoff_location_id
            changed = True
    if changed:
        db.commit()
