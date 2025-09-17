# backend/etest_routes.py
from flask import Blueprint, request, jsonify, current_app
import json
import os
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

etest_bp = Blueprint("etest", __name__, url_prefix="/api/etest")

def _resolve_json_path(arg_path: Optional[str]) -> str:
    """
    Resolve JSON path priority:
    1) explicit query/body 'json_path'
    2) env var ETEST_JSON_PATH
    3) sensible default for your NFS mount
    """
    if arg_path and os.path.exists(arg_path):
        return arg_path
    env_path = os.environ.get("ETEST_JSON_PATH")
    if env_path and os.path.exists(env_path):
        return env_path
    default_path = "/etestnew/SPECS/usr/aquq/etest_app/output.json"
    return default_path

def _load_json(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"JSON file not found at: {path}")
    with open(path, "r") as f:
        return json.load(f)

@etest_bp.route("/devices", methods=["GET"])
def list_devices():
    """
    Returns all device keys with their 'prb' value.
    Query params:
      - json_path (optional)
    Response: {"devices":[{"name":"DEVICEKEY","prb":"E12A" or null}, ...]}
    """
    json_path = request.args.get("json_path")
    resolved = _resolve_json_path(json_path)
    try:
        data = _load_json(resolved)
    except Exception as e:
        return jsonify({"error": str(e), "json_path": resolved}), 400

    devices = []
    for k, v in data.items():
        waf = v.get("waf", [])
        if waf:
            logging.debug(f"Device: {k}, Wafer Coordinates: {waf}")
        devices.append({"name": k, "prb": v.get("prb"), "waf": waf})

    # Sort for nice UX
    devices.sort(key=lambda d: d["name"])
    return jsonify({"devices": devices, "json_path": resolved})

@etest_bp.route("/device-mods", methods=["POST"])
def device_mods():
    """
    Body: {
      "devices": ["DEVKEY1", "DEVKEY2", ...],
      "json_path": "/custom/path/output.json"   # optional
    }
        Returns all unique mods with coordinates (if present) and which devices contributed them.
    Response:
    {
            "mods": [{"name":"c9fd_998b","x": 14000, "y": 12625, "devices":["DEVKEY1","DEVKEY2"]}, ...],
      "selected_count": 2
    }
    """
    payload = request.get_json(silent=True) or {}
    selected = payload.get("devices") or []
    json_path = payload.get("json_path")
    resolved = _resolve_json_path(json_path)

    if not isinstance(selected, list) or not all(isinstance(x, str) for x in selected):
        return jsonify({"error": "devices must be an array of strings"}), 400

    try:
        data = _load_json(resolved)
    except Exception as e:
        return jsonify({"error": str(e), "json_path": resolved}), 400

    # Build reverse index: mod -> set(devices) and capture coordinates
    mod_sources = {}
    mod_coords = {}  # first-seen coords across all selected devices
    mod_device_coords = {}  # per-device coords: {mod: {dev: {x,y}}}
    for dev in selected:
        node = data.get(dev)
        if not node:
            # ignore unknown devices; could also collect to 'missing'
            continue
        mods = node.get("mod") or []
        # Include mods as objects with `name`, `x`, and `y`
        for m in mods:
            if not isinstance(m, dict) or "name" not in m:
                continue
            mod_name = m["name"].strip()
            if not mod_name:
                continue
            mod_sources.setdefault(mod_name, set()).add(dev)
            # capture coordinates from the first occurrence; if later occurrences disagree, keep the first
            if mod_name not in mod_coords:
                x = m.get("x")
                y = m.get("y")
                if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                    mod_coords[mod_name] = {"x": x, "y": y}
            # also record per-device coordinates
            x = m.get("x")
            y = m.get("y")
            if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                mod_device_coords.setdefault(mod_name, {})[dev] = {"x": x, "y": y}

    # Format output
    mods_list = []
    single_dev = selected[0] if len(selected) == 1 else None
    for m, srcs in mod_sources.items():
        info = {"name": m, "devices": sorted(list(srcs))}
        # Prefer coords for the single selected device, if only one dev is selected
        coords = None
        if single_dev:
            coords = mod_device_coords.get(m, {}).get(single_dev)
        if not coords:
            coords = mod_coords.get(m)
        if coords:
            info.update(coords)
        mods_list.append(info)
    # Sort mods alphabetically for stable UI
    mods_list.sort(key=lambda x: x["name"])

    wafers = {dev: data.get(dev, {}).get("waf", []) for dev in selected}
    # Include wafer metadata (e.g., flat location/angle) for notch rendering
    wafer_meta = {}
    for dev in selected:
        wafer_info = (data.get(dev) or {}).get("wafer") or {}
        # Only include selected fields we currently need
        meta = {
            "flatLocation": wafer_info.get("flatLocation"),
            "flatAngle_deg": wafer_info.get("flatAngle_deg"),
        }
        wafer_meta[dev] = meta
    logging.debug("Selected Devices: %s", selected)
    logging.debug("Wafers Data: %s", wafers)
    return jsonify({
        "mods": mods_list,
        "wafers": wafers,
        "waferMeta": wafer_meta,
        "selected_count": len(selected)
    })
