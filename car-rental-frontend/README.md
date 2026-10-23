# Septum Rental Frontend v2

Modern Next.js/TypeScript frontend for the Septum Rental API.

## Important

The frontend runs on **port 3001** by default:

```powershell
npm.cmd run dev
```

Open:

```text
http://localhost:3001
```

The backend must allow this origin in CORS. Use the included Septum API v2.3 update or add:

```python
"http://localhost:3001",
"http://127.0.0.1:3001",
```

to `allow_origins`.

## Start

Backend terminal:

```powershell
python -m uvicorn app.main:app --reload --reload-dir app
```

Frontend terminal:

```powershell
npm.cmd install
npm.cmd run dev
```

## UX

The homepage centers around:

- WANN – search by rental period
- WO – search by location
- WAS – search by brand, model or vehicle type

## Branding

Brand name: **SEPTUM**

## API

Default:

```text
http://127.0.0.1:8000
```

Optional `.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```


## v3 imagery

Vehicle imagery now comes primarily from the API field `image_url`.

This means:

- fleet units can have different photos even when brand/model are identical;
- the frontend no longer assigns one generic landscape/photo to many unrelated vehicles;
- fictional demo vehicles are visibly marked `DEMO / FICTIONAL`;
- the type selector shows how many vehicles exist for each type;
- vehicle types with zero entries are disabled rather than silently returning an empty list.

Use API v2.4 together with this frontend.


## v3.1 hero turntable

The Porsche hero now cycles automatically through three real 911 GT3 RS
perspectives every 2.6 seconds. A perspective/rotateY transition creates a
turntable-like motion similar to the rotating showcase object in the reference
animation. The three indicators below the hero image can also be clicked.


## v4
The hero is fixed to the Porsche 911 GT3 RS and uses a real embedded 3D model with automatic 360-degree rotation, not a 2D image pan. Vehicle cards and the booking dialog now show technical specifications. Random image services are no longer used; unverified images render as a branded placeholder instead of a wrong photo.


## v6 consumer UX

- Restores the dark space-inspired SEPTUM visual language from the original reference short.
- The Porsche hero automatically cycles through the real CarShow360/Samar photo series on the main page; the customer does not need to drag it.
- Selecting **Alle Typen** with empty brand/model searches the entire active fleet.
- Entire vehicle cards are clickable and open checkout.
- Booking images use `object-fit: contain` so bicycles, aircraft and other tall/wide subjects are not cropped.
- Checkout requires login/registration first. No dropdown of other customers exists.
- Session auth uses the API v2.9 Bearer token and persists in localStorage.
- Technical API status indicators were removed from the customer-facing header.


## v6.1 customer API separation

The consumer website no longer uses the management `/bookings` endpoint.
Customer bookings are created via `/customer/bookings`, while the internal
Swagger management API remains unrestricted for the operator during local development.


## v6.2 photoreal automatic 360 hero
The Porsche hero now embeds Auto View Point's real-capture 360 tour and starts the hosted guided tour automatically in a loop. The embed is non-interactive on the landing page, so the customer does not need to drag the car manually. The stage around the tour is masked and blended into SEPTUM's dark orbital background.

The consumer frontend still uses only `/auth/*` and `/customer/*` for private customer operations. The management Swagger API remains separate and unrestricted for the operator.


## v6.3
- Consumer catalog now uses `/catalog/vehicles` and `/catalog/locations`; management endpoints are admin-only in API v3.2.
- Booking modal shows rental subtotal, EUR 500 transfer fee when required, effective vehicle location at rental start, and final total before confirmation.
- Long source URLs are shown as compact `Specs`, `Bild` and `360°` links.
- Modal images use `object-fit: contain`; failed images fall back cleanly instead of showing a broken image icon.


## v6.4 live immutable quote UX
Changing dates or locations immediately invalidates the visible quote and requests a fresh server-side quote. The booking button stays disabled while recalculation is running and only accepts a quote that exactly matches the current selection. Final pricing is recalculated by the backend again on booking creation.


## GitHub Pages

The existing frontend is published at **https://eige90.github.io/Septem/**.
The `Deploy SEPTUM frontend to GitHub Pages` workflow runs on frontend changes to
`main` and can also be started manually in GitHub Actions.

With `GITHUB_PAGES=true`, Next.js exports the frontend to `out/` and uses
`/Septem` as its base path. Local `npm run dev` keeps its existing configuration
and port 3001.

The public API connection is intentionally left unconfigured for now. The
interface loads, while catalog data, login and booking require a backend.
The published build does not send requests to the visitor's localhost.

To connect an API later:

1. Set the repository Actions variable `NEXT_PUBLIC_API_BASE_URL` to the public
   HTTPS API base URL, without `/docs` or a trailing slash.
2. Allow the origin `https://eige90.github.io` in the API's CORS configuration.
3. Run the deployment workflow again; Next.js embeds this public URL at build time.

Local preview of the Pages build:

```bash
npm ci
GITHUB_PAGES=true npm run build
```

Serve `out/` beneath `/Septem/` when testing the exported files.
