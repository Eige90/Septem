import type {
  AuthResponse,
  Booking,
  BookingCreate,
  BookingQuote,
  Location,
  LoginPayload,
  RegisterPayload,
  User,
  Vehicle,
} from "@/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

const TOKEN_KEY = "septum_session";

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(message: string, status: number, detail: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

export function getStoredToken() {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function storeToken(token: string) {
  if (typeof window !== "undefined") {
    window.localStorage.setItem(TOKEN_KEY, token);
  }
}

export function clearStoredToken() {
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(TOKEN_KEY);
  }
}

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getStoredToken();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    let detail: unknown = null;
    try {
      const body = await response.json();
      detail = body.detail ?? body;
    } catch {
      detail = null;
    }

    let message = `API error ${response.status}`;
    if (typeof detail === "string") message = detail;
    if (detail && typeof detail === "object" && "message" in detail) {
      const candidate = (detail as { message?: unknown }).message;
      if (typeof candidate === "string") message = candidate;
    }
    throw new ApiError(message, response.status, detail);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

function buildQuery(params: Record<string, string | undefined>) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") searchParams.set(key, value);
  });
  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

export function getVehicles(params: Record<string, string | undefined> = {}) {
  return apiRequest<Vehicle[]>(`/catalog/vehicles${buildQuery(params)}`);
}

export function getLocations() {
  return apiRequest<Location[]>("/catalog/locations");
}

export function registerCustomer(payload: RegisterPayload) {
  return apiRequest<AuthResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function loginCustomer(payload: LoginPayload) {
  return apiRequest<AuthResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getCurrentCustomer() {
  return apiRequest<User>("/auth/me");
}

export function logoutCustomer() {
  return apiRequest<void>("/auth/logout", { method: "POST" });
}


export function getBookingQuote(payload: BookingCreate) {
  return apiRequest<BookingQuote>("/customer/bookings/quote", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createBooking(payload: BookingCreate) {
  return apiRequest<Booking>("/customer/bookings", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
