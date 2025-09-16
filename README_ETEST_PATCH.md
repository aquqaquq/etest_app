# Patch: eTest Program Generator (Devices → Mods with contributing devices)

## Files in this patch
- `backend/etest_routes.py` — Flask blueprint with:
  - `GET /api/etest/devices?json_path=...` → returns all device keys with their `prb`
  - `POST /api/etest/device-mods` (body: `{"devices":[...], "json_path":"..."}`) → returns unique mods with the list of devices that include each mod
- `frontend/src/pages/ETest.jsx` — React page
  - Lists devices (shows `prb`)
  - Lets you select multiple devices
  - "OK — Aggregate Mods" calls backend and shows a table: **mod** + **devices that contain it**
  - CSV download of the mods table

## Why "OK" might have shown nothing
- Selected list was empty (no devices checked) → now the button shows the count and is disabled when nothing is selected.
- Backend route expected different payload or path → this patch standardizes:
  - `POST /api/etest/device-mods` with JSON body `{"devices":[...], "json_path":"/etestnew/.../output.json"}`
  - The JSON path falls back to env `ETEST_JSON_PATH`, then to `/etestnew/SPECS/usr/aquq/etest_app/output.json`.
- JSON file not found or permission error → the API now returns a clear error message; the UI shows it in red.

## How to install
1) **Backend (Flask)**
   - Place `backend/etest_routes.py` somewhere within your Flask app package (e.g. `app/etest_routes.py`).
   - In your Flask app factory (or main), register the blueprint:
     ```python
     from etest_routes import etest_bp
     app.register_blueprint(etest_bp)
     ```
   - Ensure the server runs on the same port you exposed to the front-end (e.g. 8080).

2) **Frontend (Vite + React)**
   - Save `frontend/src/pages/ETest.jsx` to your React project (replace your existing ETest page).
   - Make sure your router has a route like:
     ```jsx
     <Route path="/etest" element={<ETest />} />
     ```
   - Confirm `VITE_API_URL` points to your Flask server base (e.g. `http://mnplvetest01:8080`).

3) **Environment / Path**
   - If your JSON lives at `/etestnew/.../output.json`, you can leave the UI's default path as-is.
   - Alternatively, export on the Flask VM:
     ```bash
     export ETEST_JSON_PATH=/etestnew/SPECS/usr/aquq/etest_app/output.json
     ```

## Quick endpoint tests
- List devices (server-side):
  ```bash
  curl -s "http://localhost:8080/api/etest/devices?json_path=/etestnew/SPECS/usr/aquq/etest_app/output.json" | jq .devices[0:3]
  ```
- Get mods from two devices:
  ```bash
  curl -s -X POST "http://localhost:8080/api/etest/device-mods" \
    -H "Content-Type: application/json" \
    -d '{"devices":["5CC9001ACET2","5CC9007AC"],"json_path":"/etestnew/SPECS/usr/aquq/etest_app/output.json"}' | jq .mods[0:5]
  ```

## Notes
- Large JSON is read per request for simplicity. If performance becomes an issue, we can add caching.
- Mods/devices are sorted alphabetically for stable UI.
- CSV download includes two columns: `mod` and `devices` (semicolon-separated inside the field).
