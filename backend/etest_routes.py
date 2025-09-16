# backend/etest_routes.py
from flask import Blueprint, request, jsonify, current_app
import json
import os
from typing import Optional

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

    devices = [{"name": k, "prb": v.get("prb")} for k, v in data.items()]
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
    Returns all unique mods and which devices contributed them.
    Response:
    {
      "mods": [{"name":"c9fd_998b","devices":["DEVKEY1","DEVKEY2"]}, ...],
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

    # Build reverse index: mod -> set(devices)
    mod_sources = {}
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

    # Format output
    mods_list = [{"name": m, "devices": sorted(list(srcs))}
                 for m, srcs in mod_sources.items()]
    # Sort mods alphabetically for stable UI
    mods_list.sort(key=lambda x: x["name"])

    return jsonify({
        "mods": mods_list,
        "selected_count": len(selected),
        "json_path": resolved
    })
