
# etest_patch_v5

This update ensures devices with empty or missing `mod` arrays are **never** listed in the device dropdown.

## What changed

### Backend (Flask)
- `/api/etest/devices` filters out devices whose `mod` is not a non-empty list.
- Optional `min_mods` query parameter (defaults to 1).
- Safer JSON loading and guards.

### Frontend (React)
- `ETest.jsx` requests `/api/etest/devices?min_mods=1`.
- Double client-side filtering: only show devices where `mod_count > 0`.
- Fetch mods via `/api/etest/device-mods` and render the list on OK.

## Paths / Environment
- Backend reads JSON from `ETEST_JSON_PATH` env var, or defaults to `/etestnew/SPECS/usr/aquq/etest_app/output.json`.
- Frontend respects `VITE_API_BASE` for proxying to Flask.

## Drop-in
- Replace your Flask route file with `backend/app.py`.
- Replace your React page with `frontend/src/pages/ETest.jsx` (or adapt paths).
- Restart dev servers to pick up changes.
