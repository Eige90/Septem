import type { Vehicle, VehicleType } from "@/types";

const typeLabels: Record<VehicleType, string> = {
  supercar_sport: "Supersport & Sport",
  classic_muscle: "Klassiker & Muscle",
  coupe_sedan_suv: "Coupé · Limousine · SUV",
  off_road: "Off-Road",
  motorcycle_scooter: "Motorrad & Roller",
  bicycle: "Fahrrad",
  truck_van_utility: "Lkw · Transporter · Utility",
  armored: "Armored",
  imani_tech: "Imani Tech",
  military_defense: "Military & Defense",
  helicopter: "Helikopter",
  aircraft_jet: "Flugzeug & Jet",
  boat_yacht: "Boot & Yacht",
  submarine: "U-Boot",
  amphibious: "Amphibisch",
  futuristic: "Futuristisch",
};

function commonsFile(filename: string, width = 1600) {
  const safeName = filename.trim().replaceAll(" ", "_");
  return `https://commons.wikimedia.org/wiki/Special:FilePath/${encodeURIComponent(
    safeName,
  ).replaceAll("%2F", "/")}?width=${width}`;
}

/**
 * These are category-level emergency fallbacks only.
 * Vehicle cards normally use vehicle.image_url from the API.
 * Every fallback visibly contains the relevant vehicle/object.
 */
const imageByType: Record<VehicleType, string> = {
  supercar_sport: commonsFile("Porsche 911 992 GT3 RS.jpg"),
  classic_muscle: commonsFile("2024 Ford Mustang GT.jpg"),
  coupe_sedan_suv: commonsFile(
    "2024 Mercedes-Benz E-Class E220d AMG Line.jpg",
  ),
  off_road: commonsFile("Land Rover Defender 110 (48802785268).jpg"),
  motorcycle_scooter: commonsFile("BMW R 1250 GS (1).jpg"),
  bicycle: commonsFile("Mountainbike.jpg"),
  truck_van_utility: commonsFile("MAN TGX (52839928664).jpg"),
  armored: commonsFile("GIGN-Centigon1 Domenjod 23 nov 2017.jpg"),
  imani_tech: commonsFile("Dodge Charger 2024.jpg"),
  military_defense: commonsFile(
    "Chevrolet Suburban LT GMTK2XX Diplomatic Black Armoured (3).jpg",
  ),
  helicopter: commonsFile("Airbus H125 (aircraft).jpg"),
  aircraft_jet: commonsFile("Fighter jet.png"),
  boat_yacht: commonsFile("Sunseeker.motoryacht.predator.arp.jpg"),
  submarine: commonsFile(
    "The attack submarine USS La Jolla (SSN 701) departs from Saipan, Northern Mariana Islands 130116-N-ZZ999-016.jpg",
  ),
  amphibious: commonsFile(
    "Amphibious car at St Michael's Mount harbour (7462).jpg",
  ),
  futuristic: commonsFile("Sketch of a futuristic car.png"),
};

export function getVehicleImage(vehicle: Vehicle) {
  return vehicle.image_url || null;
}

export function getTypeImage(type: VehicleType) {
  return imageByType[type];
}

export function vehicleTypeLabel(type: VehicleType) {
  return typeLabels[type] ?? type;
}

export function formatCurrency(value: string | number) {
  const amount = typeof value === "string" ? Number(value) : value;

  return new Intl.NumberFormat("de-DE", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(amount);
}


const specLabels: Record<string, string> = {
  power_hp: "Leistung",
  top_speed_kmh: "Top Speed",
  cruise_speed_kmh: "Reisegeschw.",
  flight_speed_kmh: "Fluggeschw.",
  water_speed_kmh: "Wassergeschw.",
  top_speed_knots: "Top Speed",
  weight_kg: "Gewicht",
  max_takeoff_weight_kg: "MTOW",
  max_altitude_m: "Max. Flughöhe",
  max_depth_m: "Max. Tauchtiefe",
  range_km: "Reichweite",
  acceleration_0_100_s: "0–100 km/h",
  engine: "Motor / Triebwerk",
  drivetrain: "Antrieb",
  seats: "Sitze",
  passengers: "Passagiere",
  crew: "Crew",
  length_m: "Länge",
  beam_m: "Breite",
  payload_kg: "Nutzlast",
  gross_weight_kg: "Gesamtgewicht",
  protection: "Schutz",
  technology: "Technologie",
  endurance_h: "Ausdauer",
  data_note: "Hinweis",
};

export function formatSpecLabel(key: string) {
  return specLabels[key] ?? key.replaceAll("_", " ");
}

export function formatSpecValue(key: string, value: string | number | boolean | null) {
  if (value === null) return "—";
  const units: Record<string, string> = {
    power_hp: " PS",
    top_speed_kmh: " km/h",
    cruise_speed_kmh: " km/h",
    flight_speed_kmh: " km/h",
    water_speed_kmh: " km/h",
    top_speed_knots: " kn",
    weight_kg: " kg",
    max_takeoff_weight_kg: " kg",
    max_altitude_m: " m",
    max_depth_m: " m",
    range_km: " km",
    acceleration_0_100_s: " s",
    length_m: " m",
    beam_m: " m",
    payload_kg: " kg",
    gross_weight_kg: " kg",
    endurance_h: " h",
  };
  return `${value}${units[key] ?? ""}`;
}

export function getPrimarySpecs(vehicle: Vehicle) {
  const specs = vehicle.specs ?? {};
  const priorityByType: Partial<Record<VehicleType, string[]>> = {
    supercar_sport: ["power_hp", "top_speed_kmh", "weight_kg"],
    classic_muscle: ["power_hp", "top_speed_kmh", "weight_kg"],
    coupe_sedan_suv: ["power_hp", "top_speed_kmh", "weight_kg"],
    off_road: ["power_hp", "top_speed_kmh", "weight_kg"],
    motorcycle_scooter: ["power_hp", "top_speed_kmh", "weight_kg"],
    bicycle: ["weight_kg", "top_speed_kmh", "gears"],
    truck_van_utility: ["power_hp", "payload_kg", "weight_kg"],
    armored: ["power_hp", "weight_kg", "protection"],
    imani_tech: ["power_hp", "top_speed_kmh", "technology"],
    military_defense: ["power_hp", "top_speed_kmh", "weight_kg"],
    helicopter: ["power_hp", "cruise_speed_kmh", "max_altitude_m"],
    aircraft_jet: ["cruise_speed_kmh", "max_altitude_m", "range_km"],
    boat_yacht: ["top_speed_knots", "length_m", "passengers"],
    submarine: ["max_depth_m", "weight_kg", "passengers"],
    amphibious: ["top_speed_kmh", "water_speed_kmh", "weight_kg"],
    futuristic: ["power_hp", "top_speed_kmh", "weight_kg"],
  };
  const keys = priorityByType[vehicle.vehicle_type] ?? Object.keys(specs).slice(0, 3);
  return keys
    .filter((key) => specs[key] !== undefined && specs[key] !== null)
    .slice(0, 3)
    .map((key) => ({
      key,
      label: formatSpecLabel(key),
      value: formatSpecValue(key, specs[key] as string | number | boolean | null),
    }));
}


const sourceSpecKeys = new Set(["_spec_source_url", "_image_source_url", "_360_url"]);

export function getSpecEntries(vehicle: Vehicle) {
  return Object.entries(vehicle.specs ?? {}).filter(([key]) => !sourceSpecKeys.has(key));
}

export function getSourceLinks(vehicle: Vehicle) {
  const specs = vehicle.specs ?? {};
  const links: { label: string; url: string }[] = [];
  const add = (key: string, label: string) => {
    const value = specs[key];
    if (typeof value === "string" && value.startsWith("http")) links.push({ label, url: value });
  };
  add("_spec_source_url", "Specs");
  add("_image_source_url", "Bild");
  add("_360_url", "360°");
  return links;
}
