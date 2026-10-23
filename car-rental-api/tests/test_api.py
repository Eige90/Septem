from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base, get_db
from app.main import app
from app.security import hash_password

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def admin_headers():
    response = client.post("/admin/login", json={"email": "admin@septum.example.com", "password": "StrongAdmin123!"})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def customer_headers(email="one@example.com"):
    response = client.post("/auth/register", json={
        "first_name": "Test", "last_name": "Customer", "email": email,
        "phone": None, "password": "StrongPass123!",
    })
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}, response.json()["user"]


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    db.add(models.User(first_name="SEPTUM", last_name="Admin", email="admin@septum.example.com",
                       phone=None, password_hash=hash_password("StrongAdmin123!"), role="ADMIN", active=True))
    db.commit()
    db.close()
    ah = admin_headers()
    for payload in [
        {"name":"Munich Central","address":"Street 1","city":"Munich","country":"Germany","active":True},
        {"name":"Hamburg Harbor","address":"Harbor 1","city":"Hamburg","country":"Germany","active":True},
    ]:
        assert client.post("/locations", json=payload, headers=ah).status_code == 201
    assert client.post("/vehicles", headers=ah, json={
        "brand":"Porsche","model":"911 GT3 RS","year":2018,"vehicle_type":"supercar_sport",
        "daily_rate":500,"location_id":1,"is_real_world":True,"description":"Test vehicle",
        "image_url":"https://example.com/porsche.jpg","specs":{"power_hp":520},"active":True,
    }).status_code == 201


def test_management_endpoints_require_admin():
    for path in ["/users", "/vehicles", "/locations", "/bookings", "/invoices"]:
        assert client.get(path).status_code == 401
        assert client.get(path, headers=admin_headers()).status_code == 200


def test_customer_cannot_use_admin_token_scope_and_admin_cannot_be_customer():
    ch, _ = customer_headers()
    assert client.get("/users", headers=ch).status_code == 403
    assert client.post("/auth/login", json={"email":"admin@septum.example.com","password":"StrongAdmin123!"}).status_code == 401


def test_public_catalog_is_read_only_and_available_to_customer():
    assert len(client.get("/catalog/vehicles").json()) == 1
    assert len(client.get("/catalog/locations").json()) == 2


def test_customer_only_sees_own_bookings_without_user_id():
    h1, _ = customer_headers("one@example.com")
    h2, _ = customer_headers("two@example.com")
    p1 = {"vehicle_id":1,"pickup_location_id":1,"dropoff_location_id":1,"start_date":"2026-10-10","end_date":"2026-10-12"}
    assert client.post("/customer/bookings", json=p1, headers=h1).status_code == 201
    p2 = {**p1,"start_date":"2026-10-13","end_date":"2026-10-15"}
    assert client.post("/customer/bookings", json=p2, headers=h2).status_code == 201
    rows1 = client.get("/customer/bookings", headers=h1).json()
    rows2 = client.get("/customer/bookings", headers=h2).json()
    assert len(rows1) == len(rows2) == 1
    assert "user_id" not in rows1[0]
    assert rows1[0]["id"] != rows2[0]["id"]
    assert len(client.get("/bookings", headers=admin_headers()).json()) == 2


def test_transfer_fee_is_500_when_pickup_differs_from_effective_location():
    h, _ = customer_headers()
    payload = {"vehicle_id":1,"pickup_location_id":2,"dropoff_location_id":2,"start_date":"2026-10-10","end_date":"2026-10-12"}
    quote = client.post("/customer/bookings/quote", json=payload, headers=h)
    assert quote.status_code == 200, quote.text
    data = quote.json()
    assert data["vehicle_origin_location_id"] == 1
    assert data["rental_price"] == "1000.00"
    assert data["transfer_fee"] == "500.00"
    assert data["total_price"] == "1500.00"
    created = client.post("/customer/bookings", json=payload, headers=h).json()
    assert created["transfer_fee"] == "500.00"
    assert created["total_price"] == "1500.00"


def test_next_booking_uses_previous_dropoff_as_vehicle_location():
    h1, _ = customer_headers("one@example.com")
    h2, _ = customer_headers("two@example.com")
    first = {"vehicle_id":1,"pickup_location_id":1,"dropoff_location_id":2,"start_date":"2026-10-08","end_date":"2026-10-10"}
    assert client.post("/customer/bookings", json=first, headers=h1).status_code == 201
    second = {"vehicle_id":1,"pickup_location_id":2,"dropoff_location_id":1,"start_date":"2026-10-11","end_date":"2026-10-13"}
    quote = client.post("/customer/bookings/quote", json=second, headers=h2).json()
    assert quote["vehicle_origin_location_id"] == 2
    assert quote["transfer_fee"] == "0.00"


def test_customer_cannot_read_other_booking():
    h1, _ = customer_headers("one@example.com")
    h2, _ = customer_headers("two@example.com")
    payload = {"vehicle_id":1,"pickup_location_id":1,"dropoff_location_id":1,"start_date":"2026-10-10","end_date":"2026-10-12"}
    created = client.post("/customer/bookings", json=payload, headers=h1).json()
    assert client.get(f"/customer/bookings/{created['id']}", headers=h2).status_code == 404


def test_openapi_contains_both_security_schemes():
    schema = client.get("/openapi.json").json()
    schemes = schema["components"]["securitySchemes"]
    assert schemes["CustomerBearer"]["scheme"] == "bearer"
    assert schemes["AdminBearer"]["scheme"] == "bearer"
    assert {"AdminBearer": []} in schema["paths"]["/users"]["get"]["security"]
    assert {"CustomerBearer": []} in schema["paths"]["/customer/bookings"]["get"]["security"]



def test_quote_is_read_only_and_rejects_client_price_or_status_fields():
    headers, _ = customer_headers()
    base = {
        "vehicle_id": 1,
        "pickup_location_id": 2,
        "dropoff_location_id": 2,
        "start_date": "2026-11-10",
        "end_date": "2026-11-12",
    }

    for forbidden in [
        {"total_price": "1.00"},
        {"transfer_fee": "0.00"},
        {"rental_price": "1.00"},
        {"status": "CANCELLED"},
        {"user_id": 999},
    ]:
        response = client.post(
            "/customer/bookings/quote",
            json={**base, **forbidden},
            headers=headers,
        )
        assert response.status_code == 422, response.text


def test_booking_recalculates_final_price_and_rejects_client_totals():
    headers, _ = customer_headers()
    payload = {
        "vehicle_id": 1,
        "pickup_location_id": 2,
        "dropoff_location_id": 2,
        "start_date": "2026-12-10",
        "end_date": "2026-12-12",
    }

    quote = client.post(
        "/customer/bookings/quote",
        json=payload,
        headers=headers,
    )
    assert quote.status_code == 200, quote.text
    quote_data = quote.json()
    assert quote_data["total_price"] == "1500.00"
    assert quote_data["transfer_fee"] == "500.00"
    assert quote_data["start_date"] == payload["start_date"]
    assert quote_data["end_date"] == payload["end_date"]
    assert quote_data["dropoff_location_id"] == payload["dropoff_location_id"]
    assert quote_data["quote_generated_at"]

    manipulated = client.post(
        "/customer/bookings",
        json={**payload, "total_price": "1.00"},
        headers=headers,
    )
    assert manipulated.status_code == 422, manipulated.text

    created = client.post(
        "/customer/bookings",
        json=payload,
        headers=headers,
    )
    assert created.status_code == 201, created.text
    created_data = created.json()
    assert created_data["rental_price"] == quote_data["rental_price"]
    assert created_data["transfer_fee"] == quote_data["transfer_fee"]
    assert created_data["total_price"] == quote_data["total_price"]


def test_new_quote_is_generated_when_customer_changes_selection():
    headers, _ = customer_headers()
    first = {
        "vehicle_id": 1,
        "pickup_location_id": 1,
        "dropoff_location_id": 1,
        "start_date": "2027-01-10",
        "end_date": "2027-01-12",
    }
    second = {**first, "pickup_location_id": 2}

    q1 = client.post("/customer/bookings/quote", json=first, headers=headers)
    q2 = client.post("/customer/bookings/quote", json=second, headers=headers)
    assert q1.status_code == q2.status_code == 200
    assert q1.json()["transfer_fee"] == "0.00"
    assert q1.json()["total_price"] == "1000.00"
    assert q2.json()["transfer_fee"] == "500.00"
    assert q2.json()["total_price"] == "1500.00"


def test_customer_patch_cannot_change_prices_or_booking_status():
    headers, _ = customer_headers()
    payload = {
        "vehicle_id": 1,
        "pickup_location_id": 1,
        "dropoff_location_id": 1,
        "start_date": "2027-02-10",
        "end_date": "2027-02-12",
    }
    created = client.post("/customer/bookings", json=payload, headers=headers)
    assert created.status_code == 201, created.text
    booking_id = created.json()["id"]

    for forbidden in [
        {"total_price": "1.00"},
        {"transfer_fee": "0.00"},
        {"status": "CANCELLED"},
    ]:
        response = client.patch(
            f"/customer/bookings/{booking_id}",
            json=forbidden,
            headers=headers,
        )
        assert response.status_code == 422, response.text
