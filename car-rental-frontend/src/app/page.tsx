"use client";

import { useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  Bike,
  CalendarDays,
  CarFront,
  ChevronLeft,
  ChevronRight,
  CircleDot,
  Compass,
  MapPin,
  Search,
  Shield,
  Ship,
  Sparkles,
  Truck,
  X,
  Plane,
  LogIn,
  LogOut,
  UserRound,
  Mail,
  LockKeyhole,
  Eye,
  EyeOff,
} from "lucide-react";

import {
  ApiError,
  clearStoredToken,
  createBooking,
  getBookingQuote,
  getCurrentCustomer,
  getLocations,
  getStoredToken,
  getVehicles,
  loginCustomer,
  logoutCustomer,
  registerCustomer,
  storeToken,
} from "@/lib/api";
import {
  formatCurrency,
  formatSpecLabel,
  formatSpecValue,
  getPrimarySpecs,
  getSourceLinks,
  getSpecEntries,
  getTypeImage,
  getVehicleImage,
  vehicleTypeLabel,
} from "@/lib/vehiclePresentation";
import type {
  Booking,
  BookingQuote,
  Location,
  SearchMode,
  User,
  Vehicle,
  VehicleType,
} from "@/types";

const vehicleTypes: VehicleType[] = [
  "supercar_sport",
  "classic_muscle",
  "coupe_sedan_suv",
  "off_road",
  "motorcycle_scooter",
  "bicycle",
  "truck_van_utility",
  "armored",
  "imani_tech",
  "military_defense",
  "helicopter",
  "aircraft_jet",
  "boat_yacht",
  "submarine",
  "amphibious",
  "futuristic",
];

const heroFallback = {
  brand: "Porsche",
  model: "911 GT3 RS",
  image:
    "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=2200&q=92",
  rate: "499.00",
  label: "SUPERSPORT",
};






const categoryCards = [
  { label: "Supersport", type: "supercar_sport" as VehicleType, icon: CarFront },
  { label: "Off-Road", type: "off_road" as VehicleType, icon: Compass },
  { label: "Motorräder", type: "motorcycle_scooter" as VehicleType, icon: Bike },
  { label: "Utility", type: "truck_van_utility" as VehicleType, icon: Truck },
  { label: "Helikopter", type: "helicopter" as VehicleType, icon: Plane },
  { label: "Jet", type: "aircraft_jet" as VehicleType, icon: Plane },
  { label: "Yacht", type: "boat_yacht" as VehicleType, icon: Ship },
  { label: "Armored", type: "armored" as VehicleType, icon: Shield },
  { label: "Amphibisch", type: "amphibious" as VehicleType, icon: Compass },
  { label: "Futuristisch", type: "futuristic" as VehicleType, icon: Sparkles },
];

type SearchState = {
  startDate: string;
  endDate: string;
  locationId: string;
  brand: string;
  model: string;
  vehicleType: VehicleType | "";
};

const initialSearch: SearchState = {
  startDate: "",
  endDate: "",
  locationId: "",
  brand: "",
  model: "",
  vehicleType: "",
};

export default function HomePage() {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [allVehicles, setAllVehicles] = useState<Vehicle[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [currentCustomer, setCurrentCustomer] = useState<User | null>(null);
  const [authOpen, setAuthOpen] = useState(false);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [pendingBookingVehicle, setPendingBookingVehicle] = useState<Vehicle | null>(null);

  const [mode, setMode] = useState<SearchMode>("when");
  const [search, setSearch] = useState<SearchState>(initialSearch);
  const [hasSearched, setHasSearched] = useState(false);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState("");
  const [apiConnected, setApiConnected] = useState(true);

  const [bookingVehicle, setBookingVehicle] = useState<Vehicle | null>(null);
  const [bookingResult, setBookingResult] = useState<Booking | null>(null);

  useEffect(() => {
    async function bootstrap() {
      try {
        const [vehicleData, locationData] = await Promise.all([
          getVehicles({ active: "true" }),
          getLocations(),
        ]);

        setVehicles(vehicleData);
        setAllVehicles(vehicleData);
        setLocations(locationData);
        setApiConnected(true);

        if (getStoredToken()) {
          try {
            const customer = await getCurrentCustomer();
            setCurrentCustomer(customer);
          } catch {
            clearStoredToken();
          }
        }
      } catch (err) {
        setApiConnected(false);
        setError(
          err instanceof Error
            ? err.message
            : "Die API konnte nicht geladen werden.",
        );
      } finally {
        setLoading(false);
      }
    }

    bootstrap();
  }, []);



  const heroVehicle =
    allVehicles.find(
      (vehicle) =>
        vehicle.brand.toLowerCase() === "porsche" &&
        vehicle.model.toLowerCase().includes("911 gt3 rs"),
    ) ?? null;

  const heroLocation = useMemo(() => {
    if (!heroVehicle) return null;
    return locations.find((item) => item.id === heroVehicle.location_id) ?? null;
  }, [heroVehicle, locations]);

  const heroRate = heroVehicle?.daily_rate ?? heroFallback.rate;

  function updateSearch<K extends keyof SearchState>(
    key: K,
    value: SearchState[K],
  ) {
    setSearch((current) => ({ ...current, [key]: value }));
  }

  async function executeSearch() {
    setError("");
    setSearching(true);

    try {
      const params: Record<string, string> = { active: "true" };

      if (mode === "when") {
        if (!search.startDate || !search.endDate) {
          throw new Error("Bitte Start- und Enddatum auswählen.");
        }
        if (search.endDate <= search.startDate) {
          throw new Error("Das Enddatum muss nach dem Startdatum liegen.");
        }
        params.available_from = search.startDate;
        params.available_to = search.endDate;
      }

      if (mode === "where") {
        if (!search.locationId) {
          throw new Error("Bitte einen Standort auswählen.");
        }
        params.location_id = search.locationId;
      }

      if (mode === "what") {
        // Empty brand/model/type intentionally means: show the full active fleet.
        if (search.brand) params.brand = search.brand;
        if (search.model) params.model = search.model;
        if (search.vehicleType) params.vehicle_type = search.vehicleType;
      }

      const result = await getVehicles(params);
      setVehicles(result);
      setHasSearched(true);
      setApiConnected(true);

      window.setTimeout(() => {
        document
          .getElementById("results")
          ?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 50);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Suche fehlgeschlagen.");
    } finally {
      setSearching(false);
    }
  }

  async function resetSearch() {
    setSearch(initialSearch);
    setHasSearched(false);
    setError("");

    try {
      const result = await getVehicles({ active: "true" });
      setVehicles(result);
      setAllVehicles(result);
      setApiConnected(true);
    } catch {
      setApiConnected(false);
    }
  }

  async function chooseCategory(type: VehicleType) {
    setMode("what");
    setSearch((current) => ({
      ...current,
      brand: "",
      model: "",
      vehicleType: type,
    }));

    try {
      const result = await getVehicles({
        active: "true",
        vehicle_type: type,
      });
      setVehicles(result);
      setHasSearched(true);
      document
        .getElementById("results")
        ?.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Suche fehlgeschlagen.");
    }
  }


  function requestBooking(vehicle: Vehicle) {
    setBookingResult(null);
    if (!currentCustomer) {
      setPendingBookingVehicle(vehicle);
      setAuthMode("login");
      setAuthOpen(true);
      return;
    }
    setBookingVehicle(vehicle);
  }

  async function signOut() {
    try {
      await logoutCustomer();
    } catch {
      // Local logout must still work when the API session has already expired.
    } finally {
      clearStoredToken();
      setCurrentCustomer(null);
      setBookingVehicle(null);
      setPendingBookingVehicle(null);
    }
  }

  function vehicleTypeCount(type: VehicleType) {
    return allVehicles.filter(
      (vehicle) => vehicle.vehicle_type === type && vehicle.active,
    ).length;
  }

  return (
    <main className="page-shell">
      <section className="hero">
        <div className="hero-glow" />

        <header className="topbar">
          <a className="brand" href="#">
            <span className="brand-mark">S</span>
            <span>SEPTUM</span>
          </a>

          <nav className="desktop-nav">
            <a href="#discover">Entdecken</a>
            <a href="#results">Flotte</a>
            <a href="#locations">Standorte</a>
          </nav>

          <div className="topbar-right consumer-account">
            {currentCustomer ? (
              <>
                <button className="account-pill" onClick={() => document.getElementById("results")?.scrollIntoView({ behavior: "smooth" })}>
                  <UserRound size={15} />
                  <span>{currentCustomer.first_name}</span>
                </button>
                <button className="icon-account-button" onClick={signOut} aria-label="Abmelden">
                  <LogOut size={16} />
                </button>
              </>
            ) : (
              <button
                className="account-pill"
                onClick={() => { setAuthMode("login"); setAuthOpen(true); }}
              >
                <LogIn size={15} />
                Anmelden
              </button>
            )}
          </div>
        </header>

        <div className="hero-main">
          <div className="hero-copy">
            <div className="eyebrow">
              <Sparkles size={14} />
              PREMIUM RENTAL EXPERIENCE
            </div>

            <p className="hero-index">PORSCHE 911 · 992</p>

            <h1>
              PORSCHE
              <span>911 GT3 RS</span>
            </h1>

            <p className="hero-description">
              Nicht nur ein Auto. Deine Auswahl aus Straße, Gelände, Luft und
              Wasser — exakt dann und dort, wo du sie brauchst.
            </p>

            <div className="hero-actions">
              <button
                className="primary-hero-button"
                onClick={() =>
                  document
                    .getElementById("discover")
                    ?.scrollIntoView({ behavior: "smooth" })
                }
              >
                Fahrzeug finden
                <ArrowRight size={17} />
              </button>
              <div className="hero-price">
                <span>ab</span>
                <strong>{formatCurrency(heroRate)}</strong>
                <small>/ Tag</small>
              </div>
            </div>
          </div>

          <div className="hero-visual hero-visual-spin">
            <div className="auto360-shell" aria-label="Porsche 911 GT3 RS automatische 360-Grad-Ansicht">
              <div className="auto360-orbit auto360-orbit-a" />
              <div className="auto360-orbit auto360-orbit-b" />
              <div className="auto360-frame-mask">
                <iframe
                  className="auto360-iframe"
                  title="Porsche 911 GT3 RS 360° Virtual Tour"
                  src="https://360.autoviewpoint.com/show/?m=BiapoWy8Tmu&play=1&lp=1&ts=1&wh=0&help=0&title=2&brand=0&hr=0&qs=1"
                  allow="autoplay; fullscreen; xr-spatial-tracking"
                  allowFullScreen
                  tabIndex={-1}
                />
                <div className="auto360-edge-fade auto360-edge-left" />
                <div className="auto360-edge-fade auto360-edge-right" />
                <div className="auto360-edge-fade auto360-edge-top" />
                <div className="auto360-edge-fade auto360-edge-bottom" />
              </div>

              <div className="auto360-badge">REAL CAPTURE · AUTO 360°</div>
              <div className="auto360-note">Automatischer Rundgang · keine Bedienung nötig</div>

              <div className="spin-caption auto360-caption">
                <span>PHOTO-REAL VIRTUAL TOUR · AUTO VIEW POINT</span>
                <strong>911 GT3 RS</strong>
              </div>

              <div className="spin-specs auto360-specs">
                <div><span>LEISTUNG</span><strong>520 PS</strong></div>
                <div><span>0–100</span><strong>3,2 s</strong></div>
                <div><span>TOP SPEED</span><strong>312 km/h</strong></div>
                <div><span>GEWICHT</span><strong>1.430 kg</strong></div>
              </div>
            </div>
          </div>
        </div>

        <SearchDock
          mode={mode}
          setMode={setMode}
          search={search}
          updateSearch={updateSearch}
          locations={locations}
          vehicleTypes={vehicleTypes}
          availableTypeCounts={Object.fromEntries(
            vehicleTypes.map((type) => [type, vehicleTypeCount(type)]),
          ) as Record<VehicleType, number>}
          searching={searching}
          onSearch={executeSearch}
        />

        {error && (
          <div className="floating-error">
            <X size={15} />
            {error}
          </div>
        )}
      </section>

      <section className="discover-section" id="discover">
        <div className="section-heading compact-heading">
          <div>
            <p className="eyebrow dark-eyebrow">DEIN EINSTIEG</p>
            <h2>Wann. Wo. Was.</h2>
          </div>
          <p className="section-intro">
            Starte genau mit dem, was du bereits weißt. Den Rest ergänzt Septum
            für dich.
          </p>
        </div>

        <div className="entry-grid">
          <button
            className="entry-card"
            onClick={() => {
              setMode("when");
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
          >
            <span className="entry-number">01</span>
            <CalendarDays size={26} />
            <strong>WANN</strong>
            <p>Zeitraum wählen und sofort sehen, was verfügbar ist.</p>
            <ArrowRight size={18} />
          </button>

          <button
            className="entry-card"
            onClick={() => {
              setMode("where");
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
          >
            <span className="entry-number">02</span>
            <MapPin size={26} />
            <strong>WO</strong>
            <p>Standort wählen und die dort verfügbare Flotte entdecken.</p>
            <ArrowRight size={18} />
          </button>

          <button
            className="entry-card accent-entry"
            onClick={() => {
              setMode("what");
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
          >
            <span className="entry-number">03</span>
            <CarFront size={26} />
            <strong>WAS</strong>
            <p>Marke, Modell oder Fahrzeugklasse direkt auswählen.</p>
            <ArrowRight size={18} />
          </button>
        </div>
      </section>

      <section className="category-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow dark-eyebrow">KATEGORIEN</p>
            <h2>Mehr als Autovermietung.</h2>
          </div>
        </div>

        <div className="category-grid">
          {categoryCards.map((category) => {
            const Icon = category.icon;
            return (
              <button
                key={category.type}
                className="category-card"
                onClick={() => chooseCategory(category.type)}
              >
                <img src={getTypeImage(category.type)} alt={category.label} />
                <div className="category-gradient" />
                <div className="category-content">
                  <Icon size={21} />
                  <div className="category-title-wrap">
                    <strong>{category.label}</strong>
                    <small>{vehicleTypeCount(category.type)} verfügbar</small>
                  </div>
                  <ArrowRight size={18} />
                </div>
              </button>
            );
          })}
        </div>
      </section>

      <section id="results" className="results-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow dark-eyebrow">
              {hasSearched ? "DEINE AUSWAHL" : "FEATURED FLEET"}
            </p>
            <h2>
              {hasSearched ? "Passende Fahrzeuge" : "Bereit für jede Richtung."}
            </h2>
          </div>

          {hasSearched && (
            <button className="text-button" onClick={resetSearch}>
              Suche zurücksetzen
              <X size={16} />
            </button>
          )}
        </div>

        {loading ? (
          <div className="loading-grid">
            {[1, 2, 3, 4, 5, 6].map((item) => (
              <div className="skeleton-card" key={item} />
            ))}
          </div>
        ) : !apiConnected ? (
          <div className="api-offline-panel">
            <div>
              <CircleDot size={22} />
              <strong>Flotte momentan nicht verfügbar</strong>
            </div>
            <p>
              Die Fahrzeugdaten konnten gerade nicht geladen werden. Bitte versuche es in einem Moment erneut.
            </p>
          </div>
        ) : vehicles.length === 0 ? (
          <div className="empty-state">
            <Search size={34} />
            <h3>Keine Fahrzeuge gefunden</h3>
            <p>
              Für deine Auswahl ist aktuell kein passendes Fahrzeug verfügbar.
            </p>
            <button className="primary-button" onClick={resetSearch}>
              Alle Fahrzeuge anzeigen
            </button>
          </div>
        ) : (
          <div className="vehicle-grid">
            {vehicles.map((vehicle) => {
              const location =
                locations.find((item) => item.id === vehicle.location_id) ??
                null;

              return (
                <article
                  className="vehicle-card vehicle-card-clickable"
                  key={vehicle.id}
                  role="button"
                  tabIndex={0}
                  aria-label={`${vehicle.brand} ${vehicle.model} buchen`}
                  onClick={() => requestBooking(vehicle)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") requestBooking(vehicle);
                  }}
                >
                  <div className="card-image-wrap">
                    <SafeVehicleImage vehicle={vehicle} />
                    <div className="card-overlay" />
                    <div className="card-id">
                      #{String(vehicle.id).padStart(2, "0")}
                    </div>
                    <div className="card-type">
                      {vehicleTypeLabel(vehicle.vehicle_type)}
                    </div>
                    {!vehicle.is_real_world && (
                      <div className="fictional-badge">DEMO / FICTIONAL</div>
                    )}
                  </div>

                  <div className="card-body">
                    <div>
                      <p className="card-brand">{vehicle.brand}</p>
                      <h3>{vehicle.model}</h3>
                    </div>

                    <div className="card-details">
                      <span>
                        <MapPin size={14} />
                        {location?.city ?? "Standort"}
                      </span>
                      {vehicle.year && <span>{vehicle.year}</span>}
                    </div>

                    <div className="card-specs">
                      {getPrimarySpecs(vehicle).map((spec) => (
                        <div key={spec.key}>
                          <span>{spec.label}</span>
                          <strong>{spec.value}</strong>
                        </div>
                      ))}
                    </div>

                    <div className="card-footer">
                      <div>
                        <span>ab</span>
                        <strong>{formatCurrency(vehicle.daily_rate)}</strong>
                        <small>/ Tag</small>
                      </div>

                      <button
                        className="book-button"
                        onClick={(event) => {
                          event.stopPropagation();
                          requestBooking(vehicle);
                        }}
                      >
                        Buchen
                        <ArrowRight size={17} />
                      </button>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>

      <section className="locations-section" id="locations">
        <div>
          <p className="eyebrow">SEPTUM LOCATIONS</p>
          <h2>Deine Flotte beginnt hier.</h2>
        </div>

        <div className="location-list">
          {locations.length > 0 ? (
            locations.map((location) => (
              <div className="location-row" key={location.id}>
                <span>0{location.id}</span>
                <div>
                  <strong>{location.name}</strong>
                  <small>
                    {location.city} · {location.country}
                  </small>
                </div>
                <MapPin size={18} />
              </div>
            ))
          ) : (
            <>
              <div className="location-row">
                <span>01</span>
                <div>
                  <strong>Munich Central</strong>
                  <small>Munich · Germany</small>
                </div>
                <MapPin size={18} />
              </div>
              <div className="location-row">
                <span>02</span>
                <div>
                  <strong>Berlin City</strong>
                  <small>Berlin · Germany</small>
                </div>
                <MapPin size={18} />
              </div>
              <div className="location-row">
                <span>03</span>
                <div>
                  <strong>Hamburg Harbor</strong>
                  <small>Hamburg · Germany</small>
                </div>
                <MapPin size={18} />
              </div>
            </>
          )}
        </div>
      </section>

      <section className="statement-section">
        <div className="statement-badge">
          <Shield size={18} />
          SEPTUM
        </div>
        <p>ONE FLEET. EVERY POSSIBILITY.</p>
        <h2>
          Supersport. Off-Road. Bike. Jet. Yacht. Spezialfahrzeug.
        </h2>
      </section>

      <footer>
        <div className="brand footer-brand">
          <span className="brand-mark">S</span>
          <span>SEPTUM</span>
        </div>
        <p>Premium Rental Experience</p>
        <p>FastAPI × Next.js</p>
      </footer>

      {authOpen && (
        <AuthModal
          mode={authMode}
          setMode={setAuthMode}
          onClose={() => { setAuthOpen(false); setPendingBookingVehicle(null); }}
          onAuthenticated={(auth) => {
            storeToken(auth.access_token);
            setCurrentCustomer(auth.user);
            setAuthOpen(false);
            if (pendingBookingVehicle) {
              setBookingVehicle(pendingBookingVehicle);
              setPendingBookingVehicle(null);
            }
          }}
        />
      )}

      {bookingVehicle && (
        <BookingModal
          vehicle={bookingVehicle}
          customer={currentCustomer}
          locations={locations}
          initialStartDate={search.startDate}
          initialEndDate={search.endDate}
          bookingResult={bookingResult}
          onBookingResult={setBookingResult}
          onClose={() => {
            setBookingVehicle(null);
            setBookingResult(null);
          }}
          onConflictRefresh={async () => {
            if (hasSearched) await executeSearch();
          }}
        />
      )}
    </main>
  );
}

function SearchDock({
  mode,
  setMode,
  search,
  updateSearch,
  locations,
  vehicleTypes,
  availableTypeCounts,
  searching,
  onSearch,
}: {
  mode: SearchMode;
  setMode: (mode: SearchMode) => void;
  search: SearchState;
  updateSearch: <K extends keyof SearchState>(
    key: K,
    value: SearchState[K],
  ) => void;
  locations: Location[];
  vehicleTypes: VehicleType[];
  availableTypeCounts: Record<VehicleType, number>;
  searching: boolean;
  onSearch: () => void;
}) {
  return (
    <div className="search-dock">
      <div className="search-tabs">
        <SearchTab
          active={mode === "when"}
          label="WANN"
          sublabel="Zeitraum"
          icon={<CalendarDays size={18} />}
          onClick={() => setMode("when")}
        />
        <SearchTab
          active={mode === "where"}
          label="WO"
          sublabel="Standort"
          icon={<MapPin size={18} />}
          onClick={() => setMode("where")}
        />
        <SearchTab
          active={mode === "what"}
          label="WAS"
          sublabel="Fahrzeug"
          icon={<CarFront size={18} />}
          onClick={() => setMode("what")}
        />
      </div>

      <div className="search-fields">
        {mode === "when" && (
          <>
            <label>
              <span>Von</span>
              <div className="input-shell">
                <CalendarDays size={16} />
                <input
                  type="date"
                  value={search.startDate}
                  onChange={(event) =>
                    updateSearch("startDate", event.target.value)
                  }
                />
              </div>
            </label>
            <label>
              <span>Bis</span>
              <div className="input-shell">
                <CalendarDays size={16} />
                <input
                  type="date"
                  value={search.endDate}
                  onChange={(event) =>
                    updateSearch("endDate", event.target.value)
                  }
                />
              </div>
            </label>
          </>
        )}

        {mode === "where" && (
          <label className="wide-field">
            <span>Abholstandort</span>
            <div className="input-shell">
              <MapPin size={16} />
              <select
                value={search.locationId}
                onChange={(event) =>
                  updateSearch("locationId", event.target.value)
                }
              >
                <option value="">Standort auswählen</option>
                {locations.map((location) => (
                  <option key={location.id} value={location.id}>
                    {location.name} · {location.city}
                  </option>
                ))}
              </select>
            </div>
          </label>
        )}

        {mode === "what" && (
          <>
            <label>
              <span>Marke</span>
              <div className="input-shell">
                <Search size={16} />
                <input
                  placeholder="z. B. Porsche"
                  value={search.brand}
                  onChange={(event) =>
                    updateSearch("brand", event.target.value)
                  }
                />
              </div>
            </label>

            <label>
              <span>Modell</span>
              <div className="input-shell">
                <input
                  placeholder="z. B. 911 GT3 RS"
                  value={search.model}
                  onChange={(event) =>
                    updateSearch("model", event.target.value)
                  }
                />
              </div>
            </label>

            <label>
              <span>Typ</span>
              <div className="input-shell">
                <select
                  value={search.vehicleType}
                  onChange={(event) =>
                    updateSearch(
                      "vehicleType",
                      event.target.value as VehicleType | "",
                    )
                  }
                >
                  <option value="">Alle Typen</option>
                  {vehicleTypes.map((type) => (
                    <option
                      key={type}
                      value={type}
                      disabled={availableTypeCounts[type] === 0}
                    >
                      {vehicleTypeLabel(type)} ({availableTypeCounts[type] ?? 0})
                    </option>
                  ))}
                </select>
              </div>
            </label>
          </>
        )}

        <button
          type="button"
          className="search-button"
          onClick={onSearch}
          disabled={searching}
        >
          <Search size={19} />
          {searching ? "Suche..." : "Finden"}
        </button>
      </div>
    </div>
  );
}

function SearchTab({
  active,
  label,
  sublabel,
  icon,
  onClick,
}: {
  active: boolean;
  label: string;
  sublabel: string;
  icon: React.ReactNode;
  onClick: () => void;
}) {
  return (
    <button className={active ? "search-tab active" : "search-tab"} onClick={onClick}>
      <span className="tab-icon">{icon}</span>
      <span>
        <strong>{label}</strong>
        <small>{sublabel}</small>
      </span>
    </button>
  );
}

function AuthModal({
  mode,
  setMode,
  onClose,
  onAuthenticated,
}: {
  mode: "login" | "register";
  setMode: (mode: "login" | "register") => void;
  onClose: () => void;
  onAuthenticated: (auth: import("@/types").AuthResponse) => void;
}) {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [authError, setAuthError] = useState("");

  async function submit() {
    setAuthError("");
    if (!email || !password) {
      setAuthError("Bitte E-Mail und Passwort eingeben.");
      return;
    }
    if (mode === "register" && (!firstName || !lastName)) {
      setAuthError("Bitte Vor- und Nachname eingeben.");
      return;
    }
    if (password.length < 8) {
      setAuthError("Das Passwort muss mindestens 8 Zeichen haben.");
      return;
    }

    setSubmitting(true);
    try {
      const auth = mode === "login"
        ? await loginCustomer({ email, password })
        : await registerCustomer({
            first_name: firstName,
            last_name: lastName,
            email,
            phone: phone || undefined,
            password,
          });
      onAuthenticated(auth);
    } catch (err) {
      setAuthError(err instanceof Error ? err.message : "Anmeldung fehlgeschlagen.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="modal-backdrop auth-backdrop" onMouseDown={onClose}>
      <div className="auth-modal" onMouseDown={(event) => event.stopPropagation()}>
        <button className="modal-close auth-close" onClick={onClose} aria-label="Schließen">
          <X size={19} />
        </button>

        <div className="auth-brand-panel">
          <div className="auth-brand-mark">S</div>
          <p>SEPTUM MEMBERSHIP</p>
          <h2>Deine Fahrt.<br />Dein Account.</h2>
          <span>Buche Fahrzeuge sicher, ohne dass andere Kunden deine Daten sehen.</span>
          <div className="auth-orbit orbit-a" />
          <div className="auth-orbit orbit-b" />
        </div>

        <div className="auth-form-panel">
          <div className="auth-tabs">
            <button className={mode === "login" ? "active" : ""} onClick={() => { setMode("login"); setAuthError(""); }}>Anmelden</button>
            <button className={mode === "register" ? "active" : ""} onClick={() => { setMode("register"); setAuthError(""); }}>Registrieren</button>
          </div>

          <p className="eyebrow dark-eyebrow">{mode === "login" ? "WELCOME BACK" : "CREATE ACCOUNT"}</p>
          <h2>{mode === "login" ? "Weiter zu deiner Buchung." : "In Sekunden startklar."}</h2>

          {mode === "register" && (
            <div className="auth-name-grid">
              <label><span>Vorname</span><input value={firstName} onChange={(e) => setFirstName(e.target.value)} autoComplete="given-name" /></label>
              <label><span>Nachname</span><input value={lastName} onChange={(e) => setLastName(e.target.value)} autoComplete="family-name" /></label>
            </div>
          )}

          <label className="auth-field">
            <span>E-Mail</span>
            <div><Mail size={17} /><input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" /></div>
          </label>

          {mode === "register" && (
            <label className="auth-field">
              <span>Telefon (optional)</span>
              <div><UserRound size={17} /><input value={phone} onChange={(e) => setPhone(e.target.value)} autoComplete="tel" /></div>
            </label>
          )}

          <label className="auth-field">
            <span>Passwort</span>
            <div>
              <LockKeyhole size={17} />
              <input type={showPassword ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} autoComplete={mode === "login" ? "current-password" : "new-password"} />
              <button type="button" onClick={() => setShowPassword((v) => !v)} aria-label="Passwort anzeigen">{showPassword ? <EyeOff size={16}/> : <Eye size={16}/>}</button>
            </div>
          </label>

          {authError && <div className="modal-error">{authError}</div>}

          <button className="primary-button full-button auth-submit" onClick={submit} disabled={submitting}>
            {submitting ? "Bitte warten..." : mode === "login" ? "Anmelden & weiter" : "Account erstellen & weiter"}
            <ArrowRight size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}


function SafeVehicleImage({ vehicle, className = "" }: { vehicle: Vehicle; className?: string }) {
  const [failed, setFailed] = useState(false);
  const src = getVehicleImage(vehicle);
  if (!src || failed) {
    return (
      <div className={`verified-image-placeholder ${className}`}>
        <span>SEPTUM</span>
        <strong>{vehicle.brand}</strong>
        <small>{vehicle.model}</small>
        <em>Bildquelle aktuell nicht erreichbar.</em>
      </div>
    );
  }
  return (
    <img
      className={className}
      src={src}
      alt={`${vehicle.brand} ${vehicle.model}`}
      onError={() => setFailed(true)}
    />
  );
}

function BookingModal({
  vehicle,
  customer,
  locations,
  initialStartDate,
  initialEndDate,
  bookingResult,
  onBookingResult,
  onClose,
  onConflictRefresh,
}: {
  vehicle: Vehicle;
  customer: User | null;
  locations: Location[];
  initialStartDate: string;
  initialEndDate: string;
  bookingResult: Booking | null;
  onBookingResult: (booking: Booking | null) => void;
  onClose: () => void;
  onConflictRefresh: () => Promise<void>;
}) {
  const [pickupLocationId, setPickupLocationId] = useState(
    vehicle.location_id.toString(),
  );
  const [dropoffLocationId, setDropoffLocationId] = useState(
    vehicle.location_id.toString(),
  );
  const [startDate, setStartDate] = useState(initialStartDate);
  const [endDate, setEndDate] = useState(initialEndDate);
  const [submitting, setSubmitting] = useState(false);
  const [modalError, setModalError] = useState("");
  const [quote, setQuote] = useState<BookingQuote | null>(null);
  const [quoteLoading, setQuoteLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function loadQuote() {
      if (!customer || !pickupLocationId || !dropoffLocationId || !startDate || !endDate || endDate <= startDate) {
        setQuote(null);
        return;
      }
      setQuote(null);
      setQuoteLoading(true);
      try {
        const nextQuote = await getBookingQuote({
          vehicle_id: vehicle.id,
          pickup_location_id: Number(pickupLocationId),
          dropoff_location_id: Number(dropoffLocationId),
          start_date: startDate,
          end_date: endDate,
        });
        if (!cancelled) {
          setQuote(nextQuote);
          setModalError("");
        }
      } catch (err) {
        if (!cancelled) {
          setQuote(null);
          if (err instanceof ApiError && err.status === 409) {
            setModalError("Dieses Fahrzeug ist in diesem Zeitraum bereits vergeben.");
          }
        }
      } finally {
        if (!cancelled) setQuoteLoading(false);
      }
    }
    void loadQuote();
    return () => { cancelled = true; };
  }, [customer, vehicle.id, pickupLocationId, dropoffLocationId, startDate, endDate]);

  async function submitBooking() {
    setModalError("");

    if (!customer) {
      setModalError("Bitte zuerst anmelden.");
      return;
    }

    if (!pickupLocationId || !dropoffLocationId) {
      setModalError("Bitte Abhol- und Rückgabeort auswählen.");
      return;
    }

    if (!startDate || !endDate || endDate <= startDate) {
      setModalError("Bitte einen gültigen Mietzeitraum auswählen.");
      return;
    }

    const quoteMatchesSelection =
      quote &&
      quote.vehicle_id === vehicle.id &&
      quote.pickup_location_id === Number(pickupLocationId) &&
      quote.dropoff_location_id === Number(dropoffLocationId) &&
      quote.start_date === startDate &&
      quote.end_date === endDate;

    if (!quoteMatchesSelection || quoteLoading) {
      setModalError("Der Preis wird gerade neu berechnet. Bitte einen Moment warten.");
      return;
    }

    setSubmitting(true);

    try {
      const booking = await createBooking({
        vehicle_id: vehicle.id,
        pickup_location_id: Number(pickupLocationId),
        dropoff_location_id: Number(dropoffLocationId),
        start_date: startDate,
        end_date: endDate,
      });

      onBookingResult(booking);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setModalError(
          "Dieses Fahrzeug wurde für den Zeitraum gerade vergeben. Die Ergebnisliste wird aktualisiert.",
        );
        await onConflictRefresh();
      } else {
        setModalError(
          err instanceof Error ? err.message : "Buchung fehlgeschlagen.",
        );
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="modal-backdrop" onMouseDown={onClose}>
      <div
        className="booking-modal"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <button className="modal-close" onClick={onClose}>
          <X size={20} />
        </button>

        <div className="modal-vehicle">
          <SafeVehicleImage vehicle={vehicle} className="modal-safe-image" />
          <div className="modal-image-gradient" />
          <div className="modal-vehicle-title">
            <p>{vehicle.brand}</p>
            <h2>{vehicle.model}</h2>
            <span>{formatCurrency(vehicle.daily_rate)} / Tag</span>
          </div>
        </div>

        <div className="modal-content">
          {bookingResult ? (
            <div className="success-state">
              <div className="success-icon">✓</div>
              <p className="eyebrow dark-eyebrow">BUCHUNG BESTÄTIGT</p>
              <h2>Ready to drive.</h2>
              <p>Buchung #{bookingResult.id} wurde erfolgreich angelegt.</p>
              <div className="booking-summary">
                <div>
                  <span>Miettage</span>
                  <strong>{bookingResult.rental_days}</strong>
                </div>
                <div>
                  <span>Mietpreis</span>
                  <strong>{formatCurrency(bookingResult.rental_price)}</strong>
                </div>
                <div>
                  <span>Überführung</span>
                  <strong>{formatCurrency(bookingResult.transfer_fee)}</strong>
                </div>
                <div>
                  <span>Gesamtpreis</span>
                  <strong>{formatCurrency(bookingResult.total_price)}</strong>
                </div>
              </div>
              <button className="primary-button full-button" onClick={onClose}>
                Fertig
              </button>
            </div>
          ) : (
            <>
              <p className="eyebrow dark-eyebrow">BOOK YOUR RIDE</p>
              <h2>Deine Buchung</h2>

              {vehicle.specs && (
                <div className="modal-spec-section">
                  <div className="modal-spec-heading">Technische Daten</div>
                  <div className="modal-spec-grid">
                    {getSpecEntries(vehicle).map(([key, value]) => (
                      <div key={key}>
                        <span>{formatSpecLabel(key)}</span>
                        <strong>{formatSpecValue(key, value)}</strong>
                      </div>
                    ))}
                  </div>
                  {getSourceLinks(vehicle).length > 0 && (
                    <div className="source-links">
                      <span>Quellen</span>
                      <div>
                        {getSourceLinks(vehicle).map((link) => (
                          <a key={link.label} href={link.url} target="_blank" rel="noreferrer">{link.label}</a>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              <div className="modal-form-grid">
                <div className="signed-in-customer">
                  <span>ANGEMELDET ALS</span>
                  <strong>{customer?.first_name} {customer?.last_name}</strong>
                  <small>{customer?.email}</small>
                </div>

                <label>
                  <span>Abholort</span>
                  <select
                    value={pickupLocationId}
                    onChange={(event) =>
                      setPickupLocationId(event.target.value)
                    }
                  >
                    {locations.map((location) => (
                      <option key={location.id} value={location.id}>
                        {location.name}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  <span>Rückgabeort</span>
                  <select
                    value={dropoffLocationId}
                    onChange={(event) =>
                      setDropoffLocationId(event.target.value)
                    }
                  >
                    {locations.map((location) => (
                      <option key={location.id} value={location.id}>
                        {location.name}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  <span>Von</span>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(event) => setStartDate(event.target.value)}
                  />
                </label>

                <label>
                  <span>Bis</span>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(event) => setEndDate(event.target.value)}
                  />
                </label>
              </div>


              <div className="price-breakdown">
                <div className="price-breakdown-head">
                  <span>Preisübersicht</span>
                  {quoteLoading ? (
                    <small>wird neu berechnet…</small>
                  ) : quote ? (
                    <small>serverseitig berechnet</small>
                  ) : null}
                </div>
                {quote ? (
                  <>
                    <div><span>Miete · {quote.rental_days} Tage</span><strong>{formatCurrency(quote.rental_price)}</strong></div>
                    <div className={Number(quote.transfer_fee) > 0 ? "transfer-row active" : "transfer-row"}>
                      <span>Überführung</span>
                      <strong>{Number(quote.transfer_fee) > 0 ? formatCurrency(quote.transfer_fee) : "inklusive"}</strong>
                    </div>
                    <div className="origin-note">
                      Fahrzeugstandort zum Mietbeginn: {locations.find((location) => location.id === quote.vehicle_origin_location_id)?.name ?? `#${quote.vehicle_origin_location_id}`}
                      {Number(quote.transfer_fee) > 0 && " · Abholung an anderem Standort: +500 €"}
                    </div>
                    <div className="price-total"><span>Gesamt</span><strong>{formatCurrency(quote.total_price)}</strong></div>
                    <div className="quote-lock-note">
                      Preisvorschau · Änderungen an Ort oder Zeitraum erzeugen automatisch einen neuen Quote. Beim Buchen prüft das Backend Verfügbarkeit, Standort und Preis erneut.
                    </div>
                  </>
                ) : (
                  <div className="price-placeholder">Wähle Zeitraum und Abholort für den finalen Preis.</div>
                )}
              </div>

              {modalError && <div className="modal-error">{modalError}</div>}

              <button
                className="primary-button full-button"
                onClick={submitBooking}
                disabled={submitting || quoteLoading || !quote}
              >
                {submitting ? "Buchung wird erstellt..." : "Jetzt buchen"}
                <ArrowRight size={18} />
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
