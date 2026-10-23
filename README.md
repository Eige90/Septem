# Septem — Car Rental

**Source versions / Versionen im Code:** Frontend `6.4.0` · API `3.3.0`.
**Live frontend / Live-Frontend:** https://eige90.github.io/Septem/

## English

Car Rental is a car-rental application project with a Python API backend and a separate web frontend.

### Get started

```powershell
git clone https://github.com/Eige90/Septem.git
cd Septem
```

The existing Next.js frontend is published at **https://eige90.github.io/Septem/**. Local frontend development uses `cd car-rental-frontend`, `npm ci` and `npm run dev` on port **3001**. The FastAPI backend runs separately; no public API is connected yet.

### Current status and roadmap

- [ ] Verify Python backend startup and API response on port 8000
- [ ] Connect and verify a separately hosted HTTPS API
- [ ] Document tested installation and start commands for both components
- [ ] Review the repository layout and test rental workflows end to end
- [x] Publish the existing Next.js frontend as a static export on GitHub Pages

**Frontend:** [Open SEPTUM](https://eige90.github.io/Septem/). Catalog data, login and bookings require a separately hosted API. See the [frontend deployment instructions](car-rental-frontend/README.md#github-pages).

---

## Deutsch

Car Rental ist ein Autovermietungsprojekt mit Python-API-Backend und separatem Web-Frontend.

### Repository abrufen

```powershell
git clone https://github.com/Eige90/Septem.git
cd Septem
```

Das vorhandene Next.js-Frontend wird unter **https://eige90.github.io/Septem/** veröffentlicht. Für die lokale Entwicklung: `cd car-rental-frontend`, `npm ci`, `npm run dev` auf Port **3001**. Das FastAPI-Backend läuft separat; eine öffentliche API ist noch nicht angebunden.

### Projektstatus und Roadmap

- [ ] Start des Python-Backends und API-Antwort auf Port 8000 prüfen
- [ ] Separat gehostete HTTPS-API anbinden und prüfen
- [ ] Verifizierte Installations- und Startbefehle für beide Komponenten dokumentieren
- [ ] Projektstruktur und Vermietungsabläufe vollständig testen
- [x] Vorhandenes Next.js-Frontend als statischen Export auf GitHub Pages veröffentlichen

**Frontend:** [SEPTUM öffnen](https://eige90.github.io/Septem/). Fahrzeugdaten, Anmeldung und Buchungen benötigen eine separat gehostete API. Siehe die [Deployment-Anleitung](car-rental-frontend/README.md#github-pages).

---

Built by [Eige90](https://github.com/Eige90).

## GitHub Pages / Website status

**Frontend URL:** https://eige90.github.io/Septem/

**English:** GitHub Actions builds the frontend from `car-rental-frontend/` and publishes its static export. The API is not deployed by this workflow.

**Deutsch:** GitHub Actions baut das Frontend aus `car-rental-frontend/` und veröffentlicht den statischen Export. Die API wird durch diesen Workflow nicht bereitgestellt.
