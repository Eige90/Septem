# Multi Vehicle Rental API

A portfolio REST API built with **FastAPI**, **SQLAlchemy** and **SQLite**.

Version 2.2 expands the original car-rental demo into a multi-vehicle booking system with:

- Vehicles
- Bookings
- Locations
- Users
- Invoices
- GET / POST / PUT / PATCH / DELETE
- Availability validation
- Dynamic rental pricing
- Booking conflict detection
- Invoice tax calculation
- Query filters
- Swagger / OpenAPI
- Automated tests

## Vehicle types

The API supports these categories:

- `supercar_sport`
- `classic_muscle`
- `coupe_sedan_suv`
- `off_road`
- `motorcycle_scooter`
- `bicycle`
- `truck_van_utility`
- `armored`
- `imani_tech`
- `military_defense`
- `helicopter`
- `aircraft_jet`
- `boat_yacht`
- `submarine`
- `amphibious`
- `futuristic`

The seeded catalog contains both real-world examples and clearly marked fictional/demo vehicles.

## API resources

### Users

- `GET /users`
- `GET /users/{id}`
- `POST /users`
- `PUT /users/{id}`
- `PATCH /users/{id}`
- `DELETE /users/{id}`

### Locations

- `GET /locations`
- `GET /locations/{id}`
- `POST /locations`
- `PUT /locations/{id}`
- `PATCH /locations/{id}`
- `DELETE /locations/{id}`

### Vehicles

- `GET /vehicles`
- `GET /vehicles/{id}`
- `GET /vehicles/{id}/availability`
- `POST /vehicles`
- `PUT /vehicles/{id}`
- `PATCH /vehicles/{id}`
- `DELETE /vehicles/{id}`

### Bookings

- `GET /bookings`
- `GET /bookings/{id}`
- `POST /bookings`
- `PUT /bookings/{id}`
- `PATCH /bookings/{id}`
- `DELETE /bookings/{id}`

### Invoices

- `GET /invoices`
- `GET /invoices/{id}`
- `POST /invoices`
- `PUT /invoices/{id}`
- `PATCH /invoices/{id}`
- `DELETE /invoices/{id}`

## Booking logic

Rental periods use an exclusive end date.

A booking from:

`2026-05-10` to `2026-05-15`

is five rental days.

A second confirmed booking for the same vehicle that overlaps that period is rejected with:

`409 Conflict`

## Dynamic price calculation

The frontend/client sends:

- user
- vehicle
- pickup location
- drop-off location
- start date
- end date

The client does not send the rental total.

The backend calculates:

`rental_days × daily_rate`

## Invoice calculation

Invoices are created from an existing booking.

Example:

- rental subtotal: EUR 2,500.00
- VAT: 19%
- tax: EUR 475.00
- invoice total: EUR 2,975.00

## Vehicle filtering

Examples:

```http
GET /vehicles?vehicle_type=supercar_sport
```

```http
GET /vehicles?min_price=100&max_price=500
```

```http
GET /vehicles?location_id=1
```

```http
GET /vehicles?is_real_world=true
```

```http
GET /vehicles?available_from=2026-05-10&available_to=2026-05-15
```

Filters can be combined.

## Start on Windows PowerShell

If your old V1 API is still running, stop it with:

```powershell
CTRL+C
```

Then replace the old project files with this version.

If you want a completely fresh database, delete:

```text
car_rental.db
```

Then run:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --reload-dir app
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

## Tests

```powershell
python -m pytest -q
```

## Important note about DELETE

For data integrity:

- a user with bookings cannot be deleted
- a vehicle with bookings cannot be deleted
- a location currently referenced by vehicles/bookings cannot be deleted

The API returns `409 Conflict` instead of silently destroying linked business data.


## Response ordering

All resource responses use a consistent JSON field order with `id` first.

All collection endpoints are sorted by `id` ascending by default:

- `GET /users`
- `GET /locations`
- `GET /vehicles`
- `GET /bookings`
- `GET /invoices`

Filters do not change this default ordering.


## Variant A: customer chooses a vehicle type, API returns free fleet units

`GET /vehicles` now also supports:

- `brand`
- `model`

These filters can be combined with the existing availability period.

Example:

```http
GET /vehicles?brand=Porsche&model=911%20GT3%20RS&available_from=2026-10-10&available_to=2026-10-15
```

If the fleet contains two Porsche 911 GT3 RS vehicles and vehicle `id=1` is already booked in that period, the API still returns the second free Porsche.

Each physical fleet vehicle remains a separate database row with its own `id`. Availability is always checked against that individual `vehicle_id`.

Brand and model matching are case-insensitive and allow partial text searches.


## Frontend CORS

Septum frontend v2 runs on port 3001. CORS allows localhost/127.0.0.1 on ports 3000 and 3001.


## v2.4 vehicle imagery and complete catalog

- `Vehicle` now has an optional `image_url`.
- Existing SQLite databases are migrated automatically with `ALTER TABLE`.
- Seed logic is idempotent and adds catalog entries that are missing from an existing database.
- Every supported `vehicle_type` now has at least one vehicle.
- The two Porsche 911 GT3 RS fleet units receive different photos.
- Existing custom `image_url` values are not overwritten.


## v2.5 complete fleet catalog

The seed catalog contains at least three entries for every supported vehicle
type. There are 16 vehicle types, so a fresh database contains at least 48
catalog vehicles.

Existing databases are not deleted. On startup the seed process adds catalog
models that are missing and preserves existing rows.


## v2.6 technical data
Vehicles now expose a flexible `specs` object. Existing SQLite databases are migrated automatically. The seed also removes old LoremFlickr random-image URLs and replaces verified models with fixed Wikimedia images.


## v4.1 / v2.7
All catalog categories now use real-world entries only, with curated image URLs instead of random-image services. The Porsche hero stage also uses a transparent dark-themed 3D embed so the viewer blends into the SEPTUM design more naturally.


## Version 2 Deep Research
v2.8 deep research: real-only 48+ seeded catalog, curated images, specialty-source metadata.


## v2.9 consumer authentication and privacy

- Added `/auth/register`, `/auth/login`, `/auth/me`, `/auth/logout`.
- Passwords use PBKDF2-SHA256 with a unique random salt.
- Booking and invoice endpoints require a Bearer session token.
- A booking always belongs to the authenticated customer; clients cannot choose another `user_id`.
- `GET /users` never exposes the customer directory and returns only the authenticated account.
- Existing SQLite databases are migrated without deleting `car_rental.db`.
- Example seed users are no longer created in fresh databases.


## v3.0 API split: management vs. end-consumer

The Swagger/OpenAPI API is the operator/developer management API.

Management endpoints remain directly usable in Swagger:

- `/users` — full user/customer CRUD
- `/bookings` — full booking CRUD across all customers
- `/invoices` — full invoice CRUD across all customers
- `/vehicles` and `/locations` — fleet/location CRUD

End-consumer authentication is separate:

- `/auth/register`, `/auth/login`, `/auth/me`, `/auth/logout`
- `/customer/bookings` — authenticated customer's own bookings
- `/customer/invoices` — authenticated customer's own invoices

The consumer frontend never calls the management `/users` endpoint and creates
bookings only through `/customer/bookings`.

For a later public production deployment, protect the management API behind an
admin login/API gateway/VPN or expose it only on an internal network. During local
development it intentionally stays directly usable in Swagger.


## v3.1 Swagger Bearer authentication

Customer-protected endpoints now use FastAPI's OpenAPI HTTP Bearer security scheme. Swagger shows an **Authorize** button. After `/auth/login` or `/auth/register`, copy the `access_token`, click **Authorize**, paste the token only (without `Bearer `), and Swagger adds the Authorization header automatically to `/auth/me` and `/customer/*`.


## v3.2 security, transfer fee and vehicle location timeline

- All management CRUD endpoints (`/users`, `/vehicles`, `/locations`, `/bookings`, `/invoices`) require an administrator bearer token.
- End customers only use `/auth/*`, `/customer/*` and the read-only `/catalog/*` endpoints.
- Create an administrator with: `python -m app.create_admin --email admin@example.com --password "StrongPass123!"`.
- Login as administrator with `POST /admin/login`, then use Swagger `Authorize` -> `AdminBearer`.
- A fixed EUR 500 transfer fee is added when the selected pickup location differs from the vehicle's effective location at rental start.
- The effective location is the drop-off location of the latest prior confirmed booking. Therefore a vehicle returned to Hamburg on the 10th is treated as being in Hamburg for a booking starting on the 11th.
- Completed bookings also synchronize the vehicle's current `location_id`.


## v3.3 immutable customer quotes
Customer quote/create/patch schemas now accept only customer-controlled selection fields. Client-supplied prices, transfer fees, status and user IDs are rejected with 422. Booking creation always recalculates availability, effective vehicle location, transfer fee and final total on the server.
