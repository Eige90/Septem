export type SearchMode = "when" | "where" | "what";

export type VehicleType =
  | "supercar_sport"
  | "classic_muscle"
  | "coupe_sedan_suv"
  | "off_road"
  | "motorcycle_scooter"
  | "bicycle"
  | "truck_van_utility"
  | "armored"
  | "imani_tech"
  | "military_defense"
  | "helicopter"
  | "aircraft_jet"
  | "boat_yacht"
  | "submarine"
  | "amphibious"
  | "futuristic";

export interface Vehicle {
  id: number;
  brand: string;
  model: string;
  year: number | null;
  vehicle_type: VehicleType;
  daily_rate: string;
  location_id: number;
  is_real_world: boolean;
  description: string | null;
  image_url: string | null;
  specs: Record<string, string | number | boolean | null> | null;
  active: boolean;
}

export interface Location {
  id: number;
  name: string;
  address: string;
  city: string;
  country: string;
  active: boolean;
}

export interface User {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  active: boolean;
  role: string;
  created_at: string;
}

export type BookingStatus = "CONFIRMED" | "CANCELLED";

export interface Booking {
  id: number;
  vehicle_id: number;
  pickup_location_id: number;
  dropoff_location_id: number;
  vehicle_origin_location_id: number;
  start_date: string;
  end_date: string;
  rental_days: number;
  rental_price: string;
  transfer_fee: string;
  total_price: string;
  status: BookingStatus;
  created_at: string;
}

export interface BookingQuote {
  vehicle_id: number;
  vehicle_origin_location_id: number;
  pickup_location_id: number;
  dropoff_location_id: number;
  start_date: string;
  end_date: string;
  rental_days: number;
  daily_rate: string;
  rental_price: string;
  transfer_fee: string;
  total_price: string;
  quote_generated_at: string;
}

export interface BookingCreate {
  vehicle_id: number;
  pickup_location_id: number;
  dropoff_location_id: number;
  start_date: string;
  end_date: string;
}


export interface AuthResponse {
  access_token: string;
  token_type: "bearer";
  user: User;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  password: string;
}
