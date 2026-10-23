from collections import Counter
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models


CARSHOW360_PORSCHE_URL = "https://carshow360.net/en/porsche/911/gt3-rs-vii-8628"
PORSCHE_OFFICIAL_SOURCE = (
    "https://newsroom.porsche.com/de/produkte/"
    "porsche-911-gt3-rs-saugmotor-automobilsalon-genf-weltpremiere-"
    "motorsport-weissach-aerodynamik-interieur-fahrwerk-technik-clubsport-14895.html"
)


def commons_file(filename: str, width: int = 1600) -> str:
    safe_name = filename.replace(" ", "_")
    return (
        "https://commons.wikimedia.org/wiki/"
        f"Special:FilePath/{safe_name}?width={width}"
    )


def commons_source(filename: str) -> str:
    safe_name = filename.replace(" ", "_")
    return f"https://commons.wikimedia.org/wiki/File:{safe_name}"


LOCATIONS = [
    {"name": "Munich Central", "address": "Arnulfstraße 1", "city": "Munich", "country": "Germany"},
    {"name": "Berlin City", "address": "Alexanderplatz 1", "city": "Berlin", "country": "Germany"},
    {"name": "Hamburg Harbor", "address": "Landungsbrücken", "city": "Hamburg", "country": "Germany"},
]

USERS = [
    {"first_name": "Max", "last_name": "Mustermann", "email": "max@example.com", "phone": "+49 170 1234567"},
    {"first_name": "Anna", "last_name": "Beispiel", "email": "anna@example.com", "phone": "+49 171 7654321"},
]


def item(brand, model, year, vehicle_type, daily_rate, location_name, description,
         image_filename=None, image_url=None, image_source_url=None, specs=None,
         quantity=1, image_urls=None):
    if image_filename:
        image_url = commons_file(image_filename)
        image_source_url = commons_source(image_filename)
    specs = dict(specs or {})
    if image_source_url:
        specs["_image_source_url"] = image_source_url
    return {
        "brand": brand,
        "model": model,
        "year": year,
        "vehicle_type": vehicle_type,
        "daily_rate": str(daily_rate),
        "location_name": location_name,
        "is_real_world": True,
        "description": description,
        "image_url": image_url,
        "specs": specs,
        "quantity": quantity,
        "image_urls": image_urls,
    }


VEHICLE_CATALOG = [
    # Supersport / Sport
    item("Porsche", "911 GT3 RS", 2018, "supercar_sport", "499.00", "Munich Central",
         "Track-focused Porsche 911 GT3 RS (991.2).",
         image_url="https://flib.samar.pl/600/000/638034b9021967cf88e640.webp",
         image_source_url=CARSHOW360_PORSCHE_URL,
         quantity=2,
         image_urls=[
             "https://flib.samar.pl/600/000/638034b9021967cf88e640.webp",
             "https://flib.samar.pl/600/000/6380357d25a2c5a6916640.webp",
         ],
         specs={"power_hp": 520, "top_speed_kmh": 312, "weight_kg": 1430,
                "acceleration_0_100_s": 3.2, "engine": "4.0 L flat-six naturally aspirated",
                "drivetrain": "RWD", "seats": 2, "_spec_source_url": PORSCHE_OFFICIAL_SOURCE,
                "_360_url": CARSHOW360_PORSCHE_URL}),
    item("Ferrari", "296 GTB", 2026, "supercar_sport", "699.00", "Berlin City",
         "Mid-engine plug-in hybrid supercar.", "Ferrari 296 GTB.jpg",
         specs={"power_hp": 830, "top_speed_kmh": 330, "weight_kg": 1470,
                "acceleration_0_100_s": 2.9, "engine": "3.0 L V6 twin-turbo hybrid", "seats": 2}),
    item("Lamborghini", "Huracan EVO", 2025, "supercar_sport", "749.00", "Hamburg Harbor",
         "Naturally aspirated V10 supercar.", "2021 Lamborghini Huracan Evo.jpg",
         specs={"power_hp": 640, "top_speed_kmh": 325, "weight_kg": 1422,
                "acceleration_0_100_s": 2.9, "engine": "5.2 L V10", "drivetrain": "AWD", "seats": 2}),

    # Klassiker / Muscle
    item("Ford", "Mustang GT", 2025, "classic_muscle", "189.00", "Munich Central",
         "American V8 muscle car.", "2024 Ford Mustang GT.jpg",
         specs={"power_hp": 487, "top_speed_kmh": 250, "weight_kg": 1768, "engine": "5.0 L V8", "seats": 4}),
    item("Dodge", "Challenger R/T", 2023, "classic_muscle", "199.00", "Berlin City",
         "Classic HEMI V8 coupe.", "Dodge Challenger R T.jpg",
         specs={"power_hp": 375, "top_speed_kmh": 249, "weight_kg": 1917, "engine": "5.7 L HEMI V8", "seats": 5}),
    item("Chevrolet", "Camaro SS", 2021, "classic_muscle", "209.00", "Hamburg Harbor",
         "V8 performance coupe.", "Chevrolet Camaro SS (2021) (53645289735).jpg",
         specs={"power_hp": 455, "top_speed_kmh": 290, "weight_kg": 1681, "engine": "6.2 L V8", "seats": 4}),

    # Coupé / Limousine / SUV
    item("Mercedes-Benz", "E-Class", 2024, "coupe_sedan_suv", "139.00", "Berlin City",
         "Executive sedan.", "2024 Mercedes-Benz E-Class E220d AMG Line.jpg",
         specs={"power_hp": 197, "top_speed_kmh": 238, "weight_kg": 1915, "engine": "2.0 L turbo diesel", "seats": 5}),
    item("Audi", "Q8", 2025, "coupe_sedan_suv", "179.00", "Hamburg Harbor",
         "Premium SUV coupe.", "Audi Q8.jpg",
         specs={"power_hp": 340, "top_speed_kmh": 250, "weight_kg": 2145, "engine": "3.0 L V6 turbo", "seats": 5}),
    item("BMW", "530i xDrive", 2024, "coupe_sedan_suv", "149.00", "Munich Central",
         "Current-generation executive sedan.", "BMW 5-Series (G60) 530i xDrive (2024) (53797791357).jpg",
         specs={"power_hp": 255, "top_speed_kmh": 250, "weight_kg": 1770, "engine": "2.0 L turbo", "drivetrain": "AWD", "seats": 5}),

    # Off-road
    item("Land Rover", "Defender 110", 2025, "off_road", "219.00", "Hamburg Harbor",
         "Luxury off-road vehicle.", "Land Rover Defender 110 (2020) (53977575697).jpg",
         specs={"power_hp": 250, "top_speed_kmh": 188, "weight_kg": 2303, "drivetrain": "AWD", "seats": 5}),
    item("Jeep", "Wrangler Rubicon 4xe", 2025, "off_road", "199.00", "Munich Central",
         "Plug-in hybrid trail vehicle.", "Jeep Wrangler Rubicon (JL) 4xe 1X7A0285.jpg",
         specs={"power_hp": 375, "top_speed_kmh": 177, "weight_kg": 2270, "drivetrain": "4x4", "seats": 5}),
    item("Toyota", "Land Cruiser J250", 2024, "off_road", "229.00", "Berlin City",
         "Heavy-duty all-terrain SUV.", "2024 Toyota Land Cruiser J250.jpg",
         specs={"power_hp": 205, "top_speed_kmh": 175, "weight_kg": 2330, "engine": "2.8 L turbo diesel", "seats": 5}),

    # Motorräder / Roller
    item("BMW", "R 1250 GS", 2025, "motorcycle_scooter", "119.00", "Munich Central",
         "Adventure motorcycle.", "BMW R 1250 GS (1).jpg",
         specs={"power_hp": 136, "top_speed_kmh": 219, "weight_kg": 249, "engine": "1254 cc boxer twin", "seats": 2}),
    item("Vespa", "GTS 300", 2025, "motorcycle_scooter", "55.00", "Berlin City",
         "Urban scooter.", "Vespa GTS 300 - 3 May 2026.jpg",
         specs={"power_hp": 24, "top_speed_kmh": 120, "weight_kg": 163, "engine": "278 cc single-cylinder", "seats": 2}),
    item("Ducati", "Monster 900", 2001, "motorcycle_scooter", "129.00", "Hamburg Harbor",
         "Iconic Italian naked motorcycle.", "Ducati Monster 900 (1).jpg",
         specs={"power_hp": 78, "top_speed_kmh": 210, "weight_kg": 185, "engine": "904 cc V-twin", "seats": 2}),

    # Fahrräder – real photographed brands/models
    item("Specialized", "Source Sport", 2013, "bicycle", "39.00", "Munich Central",
         "Hybrid touring bicycle.", "Specialized Source Sport-hybrid bicycle.jpg",
         specs={"bike_type": "Hybrid / touring", "frame": "Aluminium", "wheel_size_in": 28, "brakes": "Disc"}),
    item("Bianchi", "Road Bicycle", 2015, "bicycle", "49.00", "Berlin City",
         "Italian road bicycle.", "Bianchi - bicycle.jpg",
         specs={"bike_type": "Road", "frame": "Lightweight frame", "wheel_size_in": 28, "drive": "Chain"}),
    item("Brompton", "Folding Bicycle", 2012, "bicycle", "29.00", "Hamburg Harbor",
         "Compact folding city bicycle.", "Brompton bicycle (6918018132).jpg",
         specs={"bike_type": "Folding city bike", "wheel_size_in": 16, "foldable": True, "drive": "Chain"}),

    # Lkw / Transporter
    item("Mercedes-Benz", "Sprinter", 2025, "truck_van_utility", "149.00", "Munich Central",
         "Cargo van.", "Mercedes-Benz Sprinter.jpg",
         specs={"power_hp": 190, "top_speed_kmh": 160, "weight_kg": 2400, "payload_kg": 1300, "seats": 3}),
    item("MAN", "TGX", 2025, "truck_van_utility", "349.00", "Hamburg Harbor",
         "Heavy-duty tractor unit.", "MAN TGX.jpg",
         specs={"power_hp": 520, "top_speed_kmh": 90, "weight_kg": 8000, "gross_weight_kg": 18000, "seats": 2}),
    item("Ford", "Transit", 2025, "truck_van_utility", "129.00", "Berlin City",
         "Versatile utility van.", "Ford Transit T8 002.jpg",
         specs={"power_hp": 170, "top_speed_kmh": 160, "weight_kg": 2200, "payload_kg": 1300, "seats": 3}),

    # Gepanzert – real vehicles only
    item("Mercedes-Benz", "S-Guard", 2007, "armored", "649.00", "Munich Central",
         "Factory-armoured Mercedes S-Class.", "Mercedes S-Guard armoured car.jpg",
         specs={"protection": "Armoured passenger car", "body": "Luxury sedan", "seats": 5}),
    item("Land Rover", "Discovery 4 Sentinel", 2015, "armored", "579.00", "Berlin City",
         "Armoured Land Rover protection vehicle.", "Discovery 4 Sentinel at DSEi 2015.JPG",
         specs={"protection": "Armoured SUV", "drivetrain": "4x4", "seats": 5}),
    item("Centigon", "Raven 4x4", 2026, "armored", "699.00", "Hamburg Harbor",
         "Modern armoured 4x4 security vehicle.", "Centigon Raven 4x4 Eurosatory 2026.jpg",
         specs={"protection": "Armoured 4x4", "vehicle_role": "Security / protection", "drivetrain": "4x4"}),

    # Advanced Tech (API slug retained for backwards compatibility)
    item("Tesla", "Model S Plaid", 2023, "imani_tech", "359.00", "Berlin City",
         "High-performance technology-focused EV.", "2023 Tesla Model S Plaid.jpg",
         specs={"power_hp": 1020, "top_speed_kmh": 322, "weight_kg": 2162, "range_km": 600, "drivetrain": "AWD electric", "seats": 5}),
    item("Lucid", "Air Sapphire", 2024, "imani_tech", "389.00", "Munich Central",
         "Tri-motor electric performance sedan.", "Lucid Air Sapphire.jpg",
         specs={"power_hp": 1234, "top_speed_kmh": 330, "weight_kg": 2385, "range_km": 687, "drivetrain": "AWD electric", "seats": 5}),
    item("Porsche", "Taycan Turbo GT", 2025, "imani_tech", "399.00", "Hamburg Harbor",
         "High-performance 800-volt EV.", "2025 Porsche Taycan Turbo GT.png",
         specs={"power_hp": 1108, "top_speed_kmh": 305, "weight_kg": 2365, "range_km": 555, "drivetrain": "AWD electric", "seats": 4}),

    # Militär / Verteidigung – real vehicles only
    item("Oshkosh", "JLTV", 2025, "military_defense", "429.00", "Munich Central",
         "Joint Light Tactical Vehicle.", "Oshkosh JLTV.jpg",
         specs={"power_hp": 340, "top_speed_kmh": 110, "weight_kg": 10300, "vehicle_role": "Light tactical vehicle", "seats": 4}),
    item("Patria", "6x6 APC", 2025, "military_defense", "459.00", "Berlin City",
         "Protected 6x6 armoured personnel carrier.", "Patria 6x6 APC.jpg",
         specs={"power_hp": 395, "top_speed_kmh": 100, "weight_kg": 24000, "vehicle_role": "Armoured personnel carrier", "seats": 10}),
    item("Mercedes-Benz", "LAPV Enok", 2018, "military_defense", "449.00", "Hamburg Harbor",
         "Light armoured patrol vehicle.", "LAPV Enok, ILA 2018, Schoenefeld (1X7A5364).jpg",
         specs={"power_hp": 184, "top_speed_kmh": 120, "weight_kg": 5300, "vehicle_role": "Light armoured patrol vehicle", "seats": 4}),

    # Helikopter
    item("Airbus", "H125", 2026, "helicopter", "999.00", "Hamburg Harbor",
         "Light single-engine helicopter.", "Airbus H125 (aircraft).jpg",
         specs={"power_hp": 952, "cruise_speed_kmh": 252, "max_altitude_m": 7010, "max_takeoff_weight_kg": 2370, "range_km": 630, "seats": 7,
                "_spec_source_url": "https://www.airbus.com/en/products-services/helicopters/civil-helicopters/h125/h125-technical-information"}),
    item("Bell", "429", 2026, "helicopter", "1399.00", "Munich Central",
         "Twin-engine executive helicopter.", "Bell429 helicopter.jpg",
         specs={"power_hp": 1438, "cruise_speed_kmh": 278, "max_altitude_m": 6096, "max_takeoff_weight_kg": 3175, "range_km": 722, "seats": 8}),
    item("Robinson", "R44", 2026, "helicopter", "799.00", "Berlin City",
         "Four-seat light helicopter.", "Helicopter Robinson R44.jpg",
         specs={"power_hp": 245, "top_speed_kmh": 240, "max_altitude_m": 4267, "weight_kg": 683, "range_km": 560, "seats": 4}),

    # Flugzeuge / Jets
    item("Cessna", "Citation CJ4", 2026, "aircraft_jet", "2499.00", "Munich Central",
         "Light business jet.", "Cessna Citation CJ4 aircraft.jpg",
         specs={"cruise_speed_kmh": 835, "max_altitude_m": 13716, "max_takeoff_weight_kg": 7761, "range_km": 4010, "seats": 10}),
    item("Gulfstream", "G650", 2026, "aircraft_jet", "4999.00", "Berlin City",
         "Ultra-long-range business jet.", "Gulfstream G650.JPG",
         specs={"cruise_speed_kmh": 904, "top_speed_kmh": 982, "max_altitude_m": 15545, "max_takeoff_weight_kg": 45178, "range_km": 12964, "seats": 19}),
    item("Dassault", "Falcon 8X", 2026, "aircraft_jet", "4299.00", "Hamburg Harbor",
         "Long-range tri-jet business aircraft.", "Dassault Falcon 8X.jpg",
         specs={"cruise_speed_kmh": 956, "max_altitude_m": 15545, "max_takeoff_weight_kg": 33566, "range_km": 11945, "seats": 16}),

    # Boote / Yachten
    item("Sunseeker", "Predator 84", 2009, "boat_yacht", "1899.00", "Hamburg Harbor",
         "Luxury performance motor yacht.", "Sunseeker Predator 84 (7542162456).jpg",
         specs={"top_speed_knots": 38, "length_m": 25.5, "beam_m": 6.3, "passengers": 8, "engine": "Twin diesel"}),
    item("Princess", "32M", 2016, "boat_yacht", "2299.00", "Munich Central",
         "Large luxury motor yacht.", "Princess Yacht Divina Antibes.jpg",
         specs={"length_m": 32, "boat_type": "Motor yacht", "passengers": 10, "decks": 3}),
    item("Sea-Doo", "RXP", 2025, "boat_yacht", "299.00", "Berlin City",
         "High-performance personal watercraft.", "Jetskier Emäsalonselkä 2.JPG",
         specs={"power_hp": 300, "top_speed_kmh": 110, "boat_type": "Personal watercraft", "passengers": 1}),

    # U-Boote / Submersibles
    item("Deepsea Challenge", "DEEPSEA CHALLENGER", 2012, "submarine", "6999.00", "Hamburg Harbor",
         "One-person full-ocean-depth research submersible.", "Deepsea Challenger - Cité de la Mer-7935.jpg",
         specs={"max_depth_m": 11000, "weight_kg": 11800, "length_m": 8.1, "top_speed_knots": 3, "passengers": 1, "endurance_h": 56,
                "_spec_source_url": "https://www.whoi.edu/what-we-do/explore/underwater-vehicles/deepseachallenger/"}),
    item("Triton", "Limiting Factor", 2019, "submarine", "7999.00", "Munich Central",
         "Two-person full-ocean-depth submersible.", "Limiting Factor on the water surface.jpg",
         specs={"max_depth_m": 11000, "weight_kg": 12500, "passengers": 2, "endurance_h": 16,
                "_spec_source_url": "https://fivedeeps.com/home/technology/sub/"}),
    item("WHOI", "Alvin DSV-2", 2026, "submarine", "5499.00", "Berlin City",
         "Deep-ocean scientific research submersible.", "ALVIN submersible.jpg",
         specs={"max_depth_m": 6500, "weight_kg": 20000, "length_m": 7.0, "top_speed_knots": 2, "passengers": 3, "endurance_h": 10,
                "_spec_source_url": "https://ndsf.whoi.edu/alvin/specifications/"}),

    # Amphibisch – real vehicles only
    item("Gibbs", "Aquada", 2004, "amphibious", "799.00", "Hamburg Harbor",
         "High-speed amphibious car.", "Gibbs Aquada.jpg",
         specs={"power_hp": 175, "top_speed_kmh": 160, "water_speed_kmh": 50, "weight_kg": 1750, "seats": 3}),
    item("WaterCar", "Panther", 2025, "amphibious", "699.00", "Berlin City",
         "Road-going amphibious 4x4.", "WaterCar Panther at High Speeds.jpg",
         specs={"power_hp": 305, "top_speed_kmh": 130, "water_speed_kmh": 70, "weight_kg": 1780, "seats": 4}),
    item("Amphicar", "770", 1964, "amphibious", "399.00", "Munich Central",
         "Classic production amphibious car.", "Amphicar 770, 1964 (6980059884).jpg",
         specs={"power_hp": 38, "top_speed_kmh": 110, "water_speed_kmh": 12, "weight_kg": 1050, "length_m": 4.33, "seats": 4}),

    # Future Mobility – real vehicles only
    item("Rimac", "Nevera", 2026, "futuristic", "999.00", "Munich Central",
         "Electric hypercar.", "Rimac Nevera.jpg",
         specs={"power_hp": 1914, "top_speed_kmh": 412, "weight_kg": 2150, "acceleration_0_100_s": 1.81, "range_km": 490, "seats": 2}),
    item("Lotus", "Evija", 2026, "futuristic", "1099.00", "Hamburg Harbor",
         "All-electric hypercar.", "Lotus Evija (29081).jpg",
         specs={"power_hp": 2039, "top_speed_kmh": 350, "weight_kg": 1887, "range_km": 346, "seats": 2}),
    item("Tesla", "Cybertruck", 2024, "futuristic", "429.00", "Berlin City",
         "Stainless-steel electric pickup with steer-by-wire architecture.", "2024 Tesla Cybertruck.jpg",
         specs={"power_hp": 845, "top_speed_kmh": 209, "weight_kg": 3107, "range_km": 515, "drivetrain": "AWD electric", "seats": 5}),
]


DEPRECATED_DEMO_KEYS = {
    # Fictional/demo seeds from earlier versions.
    "Karin|Kuruma Armored", "Bravado|Buffalo STX", "Enus|Deity", "Obey|Omnis e-GT",
    "HVY|Nightshark", "HVY|Insurgent", "HVY|Menacer", "Mammoth|F-160 Raiju",
    "RUNE|Kosatka", "Pegassi|Toreador", "Imponte|Deluxo",
    # Superseded real seed rows whose old image/model mapping was not sufficiently curated.
    "BMW|5 Series", "Jeep|Wrangler Rubicon", "Toyota|Land Cruiser", "Ducati|Monster",
    "Trek|Marlin 7", "Specialized|Tarmac SL8", "Canyon|Grail",
    "BMW|7 Series Protection", "Mercedes-Benz|S 680 Guard", "Toyota|Land Cruiser 300 Armored",
    "Patria|6x6", "Mercedes-Benz|G 280 CDI LAPV",
    "Sunseeker|Predator", "Axopar|37 XC", "Sea-Doo|RXP-X",
    "Triton|3300/3", "U-Boat Worx|NEMO 2", "Triton|660/9 AVA", "Gibbs|Quadski",
    "Mercedes-Benz|Vision AVTR",
}


def validate_catalog_minimum() -> None:
    counts = Counter()
    for entry in VEHICLE_CATALOG:
        counts[entry["vehicle_type"]] += int(entry.get("quantity", 1))
    too_small = {key: value for key, value in counts.items() if value < 3}
    if too_small:
        raise RuntimeError(f"Every vehicle type needs at least 3 real catalog entries: {too_small}")
    if any(not entry.get("is_real_world") for entry in VEHICLE_CATALOG):
        raise RuntimeError("The deep-research catalog must contain real-world entries only.")
    if any(not entry.get("image_url") for entry in VEHICLE_CATALOG):
        raise RuntimeError("Every seeded catalog entry must have a curated image URL.")


def ensure_locations(db: Session) -> dict[str, int]:
    for data in LOCATIONS:
        existing = db.scalar(select(models.Location).where(models.Location.name == data["name"]))
        if existing is None:
            db.add(models.Location(**data, active=True))
    db.commit()
    return {
        location.name: location.id
        for location in db.scalars(select(models.Location)).all()
        if location.name in {item["name"] for item in LOCATIONS}
    }


def ensure_users(db: Session) -> None:
    # End-consumer build: accounts are created only by /auth/register.
    return


def ensure_vehicle_catalog(db: Session, location_ids: dict[str, int]) -> None:
    for raw in VEHICLE_CATALOG:
        data = dict(raw)
        location_name = data.pop("location_name")
        quantity = int(data.pop("quantity", 1))
        image_urls = list(data.pop("image_urls") or [])
        location_id = location_ids[location_name]

        existing_rows = list(db.scalars(
            select(models.Vehicle).where(
                models.Vehicle.brand == data["brand"],
                models.Vehicle.model == data["model"],
                models.Vehicle.vehicle_type == data["vehicle_type"],
            ).order_by(models.Vehicle.id.asc())
        ).all())

        while len(existing_rows) < quantity:
            index = len(existing_rows)
            image_url = image_urls[index] if index < len(image_urls) else data["image_url"]
            vehicle = models.Vehicle(
                brand=data["brand"], model=data["model"], year=data["year"],
                vehicle_type=data["vehicle_type"], daily_rate=Decimal(data["daily_rate"]),
                location_id=location_id, is_real_world=True, description=data["description"],
                image_url=image_url, specs=data["specs"], active=True,
            )
            db.add(vehicle)
            db.flush()
            existing_rows.append(vehicle)

        for index, vehicle in enumerate(existing_rows[:quantity]):
            vehicle.year = data["year"]
            vehicle.daily_rate = Decimal(data["daily_rate"])
            vehicle.location_id = location_id
            vehicle.is_real_world = True
            vehicle.description = data["description"]
            vehicle.image_url = image_urls[index] if index < len(image_urls) else data["image_url"]
            vehicle.specs = data["specs"]
            vehicle.active = True

    for vehicle in db.scalars(select(models.Vehicle)).all():
        if f"{vehicle.brand}|{vehicle.model}" in DEPRECATED_DEMO_KEYS:
            vehicle.active = False

    db.commit()


def seed_database(db: Session) -> None:
    validate_catalog_minimum()
    location_ids = ensure_locations(db)
    ensure_users(db)
    ensure_vehicle_catalog(db, location_ids)
