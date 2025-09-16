import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from etest_routes import etest_bp

app = Flask(__name__)
CORS(app)

# Register the etest blueprint
app.register_blueprint(etest_bp)

DEFAULT_JSON_PATH = os.environ.get(
    "ETEST_JSON_PATH",
    "/etestnew/SPECS/usr/aquq/etest_app/output.json"
)

_JSON_CACHE = {"path": None, "mtime": None, "data": None, "filtered": None}

def _load_json_data(path):
    """Load + cache JSON, keep only devices with non-empty mods."""
    global _JSON_CACHE
    try:
        st = os.stat(path)
    except FileNotFoundError:
        return None, None

    if (
        _JSON_CACHE["path"] != path
        or _JSON_CACHE["mtime"] != st.st_mtime
        or _JSON_CACHE["data"] is None
    ):
        with open(path, "r") as f:
            raw = json.load(f)
        # Filter: device must have a non-empty mod list
        filtered = {
            k: v
            for k, v in raw.items()
            if isinstance(v, dict)
            and isinstance(v.get("mod"), list)
            and len(v["mod"]) > 0
        }
        _JSON_CACHE.update(
            {"path": path, "mtime": st.st_mtime, "data": raw, "filtered": filtered}
        )

    return _JSON_CACHE["data"], _JSON_CACHE["filtered"]

def _get_default_json_path():
    return os.environ.get("ETEST_JSON_PATH", DEFAULT_JSON_PATH)

@app.get("/api/etest/json")
def etest_json():
    """
    Returns all device keys with non-empty mods.
    {
      "path": "...",
      "devices": ["DEV1","DEV2"],
      "count": 123
    }
    """
    path = request.args.get("path", _get_default_json_path())
    raw, filtered = _load_json_data(path)
    if raw is None:
        return jsonify({"error": "file_not_found", "path": path}), 404
    return jsonify({
        "path": path,
        "devices": sorted(filtered.keys()),
        "count": len(filtered),
    })

@app.get("/api/etest/mods")
def etest_mods():
    """
    Returns mods for a given device.
    ?device=<DEVICE_KEY>&path=<optional path>
    """
    device = request.args.get("device")
    if not device:
        return jsonify({"error": "missing_device_param"}), 400

    path = request.args.get("path", _get_default_json_path())
    raw, filtered = _load_json_data(path)
    if raw is None:
        return jsonify({"error": "file_not_found", "path": path}), 404

    entry = filtered.get(device)
    if not entry:
        return jsonify({"device": device, "mods": []})

    return jsonify({"device": device, "mods": entry.get("mod", [])})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=True)
