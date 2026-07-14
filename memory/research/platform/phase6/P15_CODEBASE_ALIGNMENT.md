# VBIE Phase 6 (pre-work) — Codebase Alignment: build INTO the existing app, not beside it

> Based on direct inspection of `/app/backend` + `/app/frontend/src` (June 2026). Architecture note; no code.

## 1. What already exists (must reuse, not duplicate)
| Concern | Reality in repo | VBIE decision |
|---------|-----------------|---------------|
| Backend shape | Thin `server.py` mounts domain routers (`reference, engines, search, ... , projects`) under `/api`; each module exposes `router` | VBIE = **new domain routers** (`entities.py`, `networking.py`, `sources.py`, `verification.py`) registered the same way. No new service. |
| DB | `core.py` → single `db` (Mongo `MONGO_URL`/`DB_NAME`) | New collections (`entities`, `relationships`, `provenance`, `sources`, `members`, `signals`, `score_history`, `brain_logs`, `geo`, `search_analytics`) on the SAME `db`. |
| Brain | `brain/` package already modular: `router.orchestrate()`, `engines.py`, `providers.py`, `context.py`, `memory.py`, `knowledge.py`, `search_layer.py`, `admin_routes.py` | Map the **5 brains onto this package** (add `collection`, `verification`, `matching`, `recommendation`, `explanation` engines) — extend, don't replace. |
| Brain cache | `db.brain_cache` + `brain_queries` + `brain_usage` ALREADY exist | Future-addition #7 is partly built → reuse `brain_cache`; add `brain_logs` for explainability (#4). |
| Identity | Firebase (`firebase_auth.py`) + `users` collection: `{uid, email, customer_id, role}`; JWT fallback; shared with DigitalOcean backend | **`members` bridge = extend `users`** with `claimed_entity_geid`. Reuse Customer ID; never fork auth. |
| Roles | `ROLE_BOOST` has `buyer/supplier/importer/exporter/cha`; references `marketplace`,`network` engines | VBIE plugs into existing role personalization. |
| Networking (web) | `Network.jsx` = placeholder `AppFeatureNote` (teaser only) | Rebuild as a **real VBIE-powered page** consuming `/api/networking` + shared Buyer Intelligence Card. |
| Adjacent pages | `Suppliers.jsx`, `Marketplace.jsx`, `Directory.jsx`, `Intelligence.jsx`, `GlobalSearch.jsx` exist | These become **views over the `entities` graph** (Supplier Intelligence = `entity_type=supplier`). |
| Frontend conventions | `@` alias, `lib/api.js`, `lib/AuthContext.jsx`, `SEO.jsx`, phosphor icons, shadcn ui | Follow exactly; add `lib/vbieApi.js` + Buyer Card component reused web+app. |
| Startup | `server.py` seeds collections + `_ensure_indexes()` | Add `seed_sources()` (from `sources_seed.json`) + VBIE indexes here. |
| CORS/env | from env only | unchanged. |

## 2. Decision: website architecture for ALL features (incl. VBIE)
- **One backend, one Mongo, one Brain, one identity** — already true in this repo; VBIE extends it. No microservice, no second DB.
- **Domain-router pattern** for every VBIE capability (mirrors existing `projects.py`, `events.py`, etc.).
- **Brain package is the intelligence layer** for the whole app → 5-brain modules live inside `brain/`, reusing its cache/providers/memory/knowledge.
- **`entities` (GEID) becomes the company identity** referenced by Networking, Buyer Search, Suppliers, Marketplace, Directory, Brain, and future Supplier Intelligence — replacing per-page ad-hoc data.
- **Mobile app** consumes the same `/api` (same endpoints) — thin client parity.

## 3. Open questions before Phase 6 build design (need from user)
1. **Mobile app repo** — not in this pod (this is the website). Where does the Expo app live, and does it call the same `REACT_APP_BACKEND_URL`/`/api` base? Any existing Networking data model there?
2. **DigitalOcean identity backend** — which collections/endpoints does it OWN (users? auth?) vs. this backend? Confirm `users.customer_id` is the shared Customer ID across web+app+DO.
3. **Networking today** — is there any real member data live in the app (profiles, connections), or is it greenfield? (Web is a stub; app unknown.)
4. Confirm VBIE collections may be added to the **same shared Mongo** (they will be new collections; won't touch `users`/auth).

## 4. What the "app emergence prompt" should contain (if you send one)
- Mobile app folder tree (Expo), its API client, and auth flow.
- The DO backend's route list + which DB/collections it manages.
- Any existing `networking`/`connections`/`members` collections + their shapes.
- Confirmation of the shared `users` schema fields.
With those, Phase 6 can specify exact shared endpoints + the `members`↔`entities` linkage + the reusable Buyer Intelligence Card for both clients — with zero duplication.
