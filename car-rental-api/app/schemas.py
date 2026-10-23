from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class VehicleType(str, Enum):
    SUPERCAR_SPORT = "supercar_sport"
    CLASSIC_MUSCLE = "classic_muscle"
    COUPE_SEDAN_SUV = "coupe_sedan_suv"
    OFF_ROAD = "off_road"
    MOTORCYCLE_SCOOTER = "motorcycle_scooter"
    BICYCLE = "bicycle"
    TRUCK_VAN_UTILITY = "truck_van_utility"
    ARMORED = "armored"
    IMANI_TECH = "imani_tech"
    MILITARY_DEFENSE = "military_defense"
    HELICOPTER = "helicopter"
    AIRCRAFT_JET = "aircraft_jet"
    BOAT_YACHT = "boat_yacht"
    SUBMARINE = "submarine"
    AMPHIBIOUS = "amphibious"
    FUTURISTIC = "futuristic"


class BookingStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class InvoiceStatus(str, Enum):
    OPEN = "OPEN"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


# -------------------------
# USERS
# -------------------------

class UserBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=50)
    active: bool = True


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserPut(UserBase):
    pass


class UserPatch(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=80)
    last_name: str | None = Field(default=None, min_length=1, max_length=80)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    active: bool | None = None




class AdminUserCreate(UserBase):
    password: str | None = Field(default=None, min_length=8, max_length=128)


class AdminUserPut(UserBase):
    password: str | None = Field(default=None, min_length=8, max_length=128)


class AdminUserPatch(UserPatch):
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None
    role: str
    active: bool
    created_at: datetime




class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=50)
    password: str = Field(min_length=8, max_length=128)


class AuthRead(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


# -------------------------
# LOCATIONS
# -------------------------

class LocationBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    address: str = Field(min_length=1, max_length=255)
    city: str = Field(min_length=1, max_length=120)
    country: str = Field(min_length=1, max_length=120)
    active: bool = True


class LocationCreate(LocationBase):
    pass


class LocationPut(LocationBase):
    pass


class LocationPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    address: str | None = Field(default=None, min_length=1, max_length=255)
    city: str | None = Field(default=None, min_length=1, max_length=120)
    country: str | None = Field(default=None, min_length=1, max_length=120)
    active: bool | None = None


class LocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    address: str
    city: str
    country: str
    active: bool


# -------------------------
# VEHICLES
# -------------------------

class VehicleBase(BaseModel):
    brand: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=120)
    year: int | None = Field(default=None, ge=1886, le=2100)
    vehicle_type: VehicleType
    daily_rate: Decimal = Field(gt=0)
    location_id: int
    is_real_world: bool = True
    description: str | None = None
    image_url: str | None = Field(default=None, max_length=1000)
    specs: dict[str, str | int | float | bool | None] | None = None
    active: bool = True


class VehicleCreate(VehicleBase):
    pass


class VehiclePut(VehicleBase):
    pass


class VehiclePatch(BaseModel):
    brand: str | None = Field(default=None, min_length=1, max_length=100)
    model: str | None = Field(default=None, min_length=1, max_length=120)
    year: int | None = Field(default=None, ge=1886, le=2100)
    vehicle_type: VehicleType | None = None
    daily_rate: Decimal | None = Field(default=None, gt=0)
    location_id: int | None = None
    is_real_world: bool | None = None
    description: str | None = None
    image_url: str | None = Field(default=None, max_length=1000)
    specs: dict[str, str | int | float | bool | None] | None = None
    active: bool | None = None


class VehicleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    brand: str
    model: str
    year: int | None
    vehicle_type: VehicleType
    daily_rate: Decimal
    location_id: int
    is_real_world: bool
    description: str | None
    image_url: str | None
    specs: dict[str, str | int | float | bool | None] | None
    active: bool


# -------------------------
# BOOKINGS
# -------------------------

class BookingBase(BaseModel):
    vehicle_id: int
    pickup_location_id: int
    dropoff_location_id: int
    start_date: date
    end_date: date
    status: BookingStatus = BookingStatus.CONFIRMED

    @model_validator(mode="after")
    def validate_period(self):
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be later than start_date")
        return self


class BookingCreate(BookingBase):
    pass


class BookingPut(BookingBase):
    pass


class BookingPatch(BaseModel):
    vehicle_id: int | None = None
    pickup_location_id: int | None = None
    dropoff_location_id: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: BookingStatus | None = None


class CustomerBookingRequest(BaseModel):
    """Customer-controlled booking inputs only.

    Prices, transfer fees, status and ownership are deliberately not accepted.
    They are calculated/assigned by the server.
    """

    model_config = ConfigDict(extra="forbid")

    vehicle_id: int
    pickup_location_id: int
    dropoff_location_id: int
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_period(self):
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be later than start_date")
        return self


class CustomerBookingPatch(BaseModel):
    """Fields a customer may change on their own booking.

    Server-calculated prices and booking status are intentionally excluded.
    """

    model_config = ConfigDict(extra="forbid")

    vehicle_id: int | None = None
    pickup_location_id: int | None = None
    dropoff_location_id: int | None = None
    start_date: date | None = None
    end_date: date | None = None



class AdminBookingCreate(BookingBase):
    user_id: int


class AdminBookingPut(BookingBase):
    user_id: int


class AdminBookingPatch(BookingPatch):
    user_id: int | None = None


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    vehicle_id: int
    pickup_location_id: int
    dropoff_location_id: int
    start_date: date
    end_date: date
    rental_days: int
    vehicle_origin_location_id: int
    rental_price: Decimal
    transfer_fee: Decimal
    total_price: Decimal
    status: BookingStatus
    created_at: datetime


class CustomerBookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vehicle_id: int
    pickup_location_id: int
    dropoff_location_id: int
    vehicle_origin_location_id: int
    start_date: date
    end_date: date
    rental_days: int
    rental_price: Decimal
    transfer_fee: Decimal
    total_price: Decimal
    status: BookingStatus
    created_at: datetime


class BookingQuoteRead(BaseModel):
    vehicle_id: int
    vehicle_origin_location_id: int
    pickup_location_id: int
    dropoff_location_id: int
    start_date: date
    end_date: date
    rental_days: int
    daily_rate: Decimal
    rental_price: Decimal
    transfer_fee: Decimal
    total_price: Decimal
    quote_generated_at: datetime


class AvailabilityRead(BaseModel):
    vehicle_id: int
    available: bool
    start_date: date
    end_date: date
    rental_days: int
    daily_rate: Decimal
    total_price: Decimal


# -------------------------
# INVOICES
# -------------------------

class InvoiceCreate(BaseModel):
    booking_id: int
    tax_rate: Decimal = Field(default=Decimal("19.00"), ge=0, le=100)
    due_date: date


class InvoicePut(BaseModel):
    booking_id: int
    tax_rate: Decimal = Field(ge=0, le=100)
    due_date: date
    status: InvoiceStatus


class InvoicePatch(BaseModel):
    tax_rate: Decimal | None = Field(default=None, ge=0, le=100)
    due_date: date | None = None
    status: InvoiceStatus | None = None


class InvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    booking_id: int
    user_id: int
    subtotal: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: InvoiceStatus
    issued_at: datetime
    due_date: date
    paid_at: datetime | None


class CustomerInvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    booking_id: int
    subtotal: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: InvoiceStatus
    issued_at: datetime
    due_date: date
    paid_at: datetime | None
