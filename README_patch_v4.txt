
Patch v4 — Exclude devices with empty mods

Changes:
- Backend `/api/etest/devices` now filters OUT any device whose `"mod"` is missing or an empty list.
- Frontend `ETest.jsx` also applies a safety filter client‑side (`mod_count > 0`) in case your server is still on an older route build.
- Nothing else in the API changed; existing integration still works.

Install:
1) Backend
   - Copy `backend/etest_routes.py` into your Flask app.
   - Register the blueprint once (usually in app factory):
       from etest_routes import etest_bp
       app.register_blueprint(etest_bp)

   - Optionally set env var:
       export ETEST_JSON_PATH=/etestnew/SPECS/usr/aquq/etest_app/output.json

2) Frontend
   - Replace your React page at `frontend/src/pages/ETest.jsx` with this file.
   - Ensure Vite env:
       VITE_API_URL=http://mnplvetest01:8080
     (or leave empty if the frontend is served by the same Flask origin during dev/proxy.)

3) Test
   - GET  /api/etest/devices?json_path=/etestnew/SPECS/usr/aquq/etest_app/output.json
   - POST /api/etest/device-mods with body {"devices":["..."],"json_path":"..."}

