import os
import json
import re
import pandas as pd

# -------- helpers reused/added --------

def parse_waf_coords(wafer_file_path):
    """
    Read wafer file and return wafer die grid coordinates like ['2,4', '3,4', ...].
    Coordinates are taken from lines that start with a number and treat the first
    whitespace-separated token as 'Column,Row'.
    """
    if not os.path.isfile(wafer_file_path):
        return []
    coords = []
    with open(wafer_file_path, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    # typical files have multiple "(table end)"; the die map often appears after the 2nd one
    parts = text.split('(table end)')
    lines = parts[2].splitlines() if len(parts) >= 3 else text.splitlines()
    for line in lines:
        if re.match(r'^\s*\d', line):
            t = re.split(r'\s+', line.strip())
            if t and ',' in t[0]:
                coords.append(t[0])
    return coords

def _to_num(s):
    try:
        v = float(str(s))
        return int(v) if v.is_integer() else v
    except Exception:
        return None

def extract_data(pattern, text, default_value=""):
    m = re.search(pattern, text)
    return m.group(1).strip() if m else default_value

# ---------- robust DIE parser (PRIMARY for module XY) ----------
def parse_mod_coords_from_die(die_file_path):
    """
    Parse module coordinates from the DIE file.
    Strategy: for each data line, take the first token as module name
    and the LAST TWO numeric tokens on the line as X and Y.
    """
    mods = {}
    if not os.path.isfile(die_file_path):
        return mods

    with open(die_file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = [ln.rstrip("\n") for ln in f if "table end" not in ln]

    # find the '*' header marker; data starts 2 lines after (fallback to 0 if not found)
    start_idx = None
    for i, ln in enumerate(lines):
        if ln.startswith("*"):
            start_idx = i + 2
            break
    if start_idx is None:
        start_idx = 0

    for ln in lines[start_idx:]:
        if ln.startswith("*") or not ln.strip():
            continue
        parts = ln.split()
        if not parts:
            continue
        name = parts[0].strip('`')  # strip optional backticks
        nums = re.findall(r'-?\d+(?:\.\d+)?', ln)
        if len(nums) >= 2:
            x = _to_num(nums[-2])
            y = _to_num(nums[-1])
            if x is not None and y is not None:
                mods[name] = (x, y)
    return mods

# ---------- DIETEST parser (FALLBACK for module XY) ----------
def parse_mod_coords_from_dietest(dietest_file_path):
    """
    Fallback parser for DIETEST:
    1) Prefer labeled values (X: <num>, Y: <num>) if present on the line.
    2) Else, use the last two numeric tokens.
    """
    mods = {}
    start_extracting = False
    rx_x = re.compile(r'\bX\s*[:=]\s*(-?\d+(?:\.\d+)?)', re.IGNORECASE)
    rx_y = re.compile(r'\bY\s*[:=]\s*(-?\d+(?:\.\d+)?)', re.IGNORECASE)

    with open(dietest_file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for raw in f:
            line = raw.strip()
            if "-" in line and "B" in line:  # heuristic for table start
                start_extracting = True
                continue
            if "table end" in line and start_extracting:
                start_extracting = False
                continue
            if not start_extracting or not line:
                continue

            name = line.split(":")[0].strip()
            x_match = rx_x.search(line)
            y_match = rx_y.search(line)
            if x_match and y_match:
                x = _to_num(x_match.group(1))
                y = _to_num(y_match.group(1))
                if x is not None and y is not None:
                    mods[name] = (x, y)
                    continue
            nums = re.findall(r'-?\d+(?:\.\d+)?', line)
            if len(nums) >= 2:
                x = _to_num(nums[-2])
                y = _to_num(nums[-1])
                if x is not None and y is not None:
                    mods[name] = (x, y)
    return mods

# ---------- Wafer/WaferTest/DIE metadata ----------
def parse_wafer_header_and_info(wafer_file_path):
    """
    Returns header_info (desc, created, revised) and wafer_info
    (stepX_um, stepY_um, flatLocation, flatAngle_deg).
    """
    header_info = {"desc": "", "created": "", "revised": ""}
    wafer_info  = {"stepX_um": None, "stepY_um": None, "flatLocation": "", "flatAngle_deg": 0}

    if not os.path.isfile(wafer_file_path):
        return header_info, wafer_info

    with open(wafer_file_path, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()

    header_info["desc"]    = extract_data(r'Desc:\s+(.*)', text, "")
    header_info["created"] = extract_data(r'Creation Date:\s+(.*)', text, "")
    header_info["revised"] = extract_data(r'Revision Date:\s+(.*)', text, "")

    step_x = extract_data(r'Die X Step:\s+(\d+)', text, "")
    step_y = extract_data(r'Die Y Step:\s+(\d+)', text, "")
    flat_loc = extract_data(r'Flat Location\s*\(T,B,L,R\):\s*([TBLR])', text, "")

    wafer_info["stepX_um"] = int(step_x) if step_x else None
    wafer_info["stepY_um"] = int(step_y) if step_y else None
    wafer_info["flatLocation"] = flat_loc
    wafer_info["flatAngle_deg"] = {"L": 270, "R": 90, "T": 0, "B": 180}.get(flat_loc, 0)

    return header_info, wafer_info

def parse_wafertest_info(wafertest_file_path):
    """
    Returns wafer test info including align die and align module name.
    """
    wt = {
        "waferType": "",
        "probeCard": "",
        "alignDie": {"x": 0, "y": 0},
        "alignModule": ""
    }
    if not os.path.isfile(wafertest_file_path):
        return wt

    with open(wafertest_file_path, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()

    wt["waferType"] = extract_data(r'WaferType:\s+(.*)', text, "")
    wt["probeCard"] = extract_data(r'ProbeCard:\s+(.*)', text, "")
    align_die = extract_data(r'Align Die:\s+(\d+,\d+)', text, "")
    if align_die:
        try:
            dx, dy = map(int, align_die.split(","))
            wt["alignDie"] = {"x": dx, "y": dy}
        except Exception:
            pass
    wt["alignModule"] = extract_data(r'Align Module:\s+(.*)', text, "")
    return wt

def parse_align_module_xy_from_die(die_file_path, align_module_name):
    """
    Find the align module row in DIE and return its X,Y (µm) using the last two numbers on that line.
    """
    if not align_module_name or not os.path.isfile(die_file_path):
        return {"x": None, "y": None}

    pat = re.compile(rf'^\s*`?{re.escape(align_module_name)}`?\b', re.IGNORECASE)
    with open(die_file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if pat.search(line):
                nums = re.findall(r'-?\d+(?:\.\d+)?', line)
                if len(nums) >= 2:
                    x = _to_num(nums[-2])
                    y = _to_num(nums[-1])
                    return {"x": x, "y": y}
    return {"x": None, "y": None}

def find_center_die_and_offsets(waf_coords, step_x, step_y):
    """
    From a list like ['2,4','3,4',...] compute center die (grid) and offsets in µm.
    Returns dict {x, y, offsetX_um, offsetY_um}
    """
    valid = [cr for cr in waf_coords if ',' in cr]
    if not valid:
        return {"x": 0, "y": 0, "offsetX_um": 0, "offsetY_um": 0}

    xs = [int(cr.split(',')[0]) for cr in valid]
    ys = [int(cr.split(',')[1]) for cr in valid]

    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    even_x = (x_max + x_min) % 2 == 0
    even_y = (y_max + y_min) % 2 == 0

    if even_x and even_y:
        cx, cy = (x_max + x_min) / 2, (y_max + y_min) / 2
        ox, oy = 0, 0
    elif even_x and not even_y:
        cx, cy = (x_max + x_min) / 2, (y_max + y_min) // 2
        ox, oy = 0, -(step_y or 0) / 2
    elif not even_x and even_y:
        cx, cy = (x_max + x_min) // 2, (y_max + y_min) / 2
        ox, oy = -(step_x or 0) / 2, 0
    else:
        cx, cy = (x_max + x_min) // 2, (y_max + y_min) // 2
        ox, oy = -(step_x or 0) / 2, -(step_y or 0) / 2

    return {"x": cx, "y": cy, "offsetX_um": ox, "offsetY_um": oy}

# -------- your main parsing, now producing mod objects + wafer metadata --------

def parse_file(file_path, wafer_root, die_root, wafertest_root, df_modules):
    """
    Builds per device:
      result['prb']  -> kept as None (unless you later parse it)
      result['mod']  -> list of {'name': str, 'x': num|None, 'y': num|None} in dependency order
      result['waf']  -> list of wafer grid strings like '2,4'
      result['wafer'] -> dict with desc/created/revised, steps, flat, align info, center die + offsets
    """
    result = {}
    prb = None
    no_colon = []
    yes_colon = []
    mod_order = []
    start_extracting = False

    filename = os.path.basename(file_path)
    wafer_file_path     = os.path.join(wafer_root, filename)
    die_file_path       = os.path.join(die_root, filename)
    wafertest_file_path = os.path.join(wafertest_root, filename)

    # 1) read DIETEST to collect module names (for ordering)
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        for raw in file:
            line = raw.strip()
            if "-" in line and "B" in line:
                start_extracting = True
            if "table end" in line and start_extracting:
                start_extracting = False
                continue
            if start_extracting and line:
                mod_name = line.split(":")[0].strip()
                # classify with your Excel rules
                rows = df_modules[df_modules['MODULE_NAME'] == mod_name]
                if not rows.empty:
                    has_colon = any(':' in ' '.join(r.astype(str).values) for _, r in rows.iterrows())
                    (yes_colon if has_colon else no_colon).append(mod_name)

    # 2) dependency-ordered module name list (same logic as before)
    for m in no_colon:
        if m not in mod_order:
            mod_order.append(m)

    temp_yes = yes_colon.copy()
    processed = set()
    while temp_yes:
        added = False
        for m in temp_yes[:]:
            rows = df_modules[df_modules['MODULE_NAME'] == m]
            depends = False
            for _, r in rows.iterrows():
                content = ' '.join(r.astype(str).values)
                for other in yes_colon:
                    if other != m and other in content and other not in processed:
                        depends = True
                        break
                if depends:
                    break
            if not depends and m not in processed:
                if m not in mod_order:
                    mod_order.append(m)
                processed.add(m)
                temp_yes.remove(m)
                added = True
        if not added:
            for m in temp_yes:
                if m not in processed:
                    if m not in mod_order:
                        mod_order.append(m)
                    processed.add(m)
            break

    # 3) get module coordinates: DIE first (robust), DIETEST as fallback
    mod_coords = parse_mod_coords_from_die(die_file_path)
    if not mod_coords:
        mod_coords = parse_mod_coords_from_dietest(file_path)

    # 4) build ordered mod objects with coords
    mod_objects = []
    seen = set()
    for name in mod_order:
        if name in seen:
            continue
        seen.add(name)
        x, y = mod_coords.get(name, (None, None))
        mod_objects.append({"name": name, "x": x, "y": y})

    # 5) wafer header + info, wafer test info, align module XY
    header_info, wafer_info = parse_wafer_header_and_info(wafer_file_path)
    wt_info = parse_wafertest_info(wafertest_file_path)
    align_mod_xy = parse_align_module_xy_from_die(die_file_path, wt_info.get("alignModule"))

    # 6) waf die grid list + center/offsets
    waf_coords = parse_waf_coords(wafer_file_path)
    center = find_center_die_and_offsets(
        waf_coords,
        wafer_info.get("stepX_um") or 0,
        wafer_info.get("stepY_um") or 0
    )

    result["prb"] = prb
    result["mod"] = mod_objects
    result["waf"] = waf_coords
    result["wafer"] = {
        "desc": header_info["desc"],
        "created": header_info["created"],
        "revised": header_info["revised"],
        "stepX_um": wafer_info["stepX_um"],
        "stepY_um": wafer_info["stepY_um"],
        "flatLocation": wafer_info["flatLocation"],
        "flatAngle_deg": wafer_info["flatAngle_deg"],
        "alignDie": wt_info["alignDie"],
        "alignModule": wt_info["alignModule"],
        "alignModuleXY_um": {"x": align_mod_xy["x"], "y": align_mod_xy["y"]},
        "centerDie": {
            "x": center["x"],
            "y": center["y"],
            "offsetX_um": center["offsetX_um"],
            "offsetY_um": center["offsetY_um"]
        }
    }
    return result

def process_folder(dietest_folder, wafer_folder, die_folder, wafertest_folder, existing_data=None):
    edr_path = r'E:\ufiles\CACH\Python_Script_Templates\C9_Master_TEST.xlsx'
    df_modules = pd.read_excel(edr_path)

    data = existing_data if existing_data else {}
    for filename in os.listdir(dietest_folder):
        file_path = os.path.join(dietest_folder, filename)
        if os.path.isfile(file_path):
            print(f"Processing file: {filename}")
            file_data = parse_file(file_path, wafer_folder, die_folder, wafertest_folder, df_modules)
            if filename in data:
                data[filename]["mod"] = file_data["mod"]
                data[filename]["waf"] = file_data["waf"]
                data[filename]["wafer"] = file_data["wafer"]
                if data[filename].get("prb") is None:
                    data[filename]["prb"] = file_data["prb"]
            else:
                data[filename] = file_data
    return data

def save_data_to_json(data, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    print(f"Data saved to {output_file} in JSON format.")

def save_data_to_text(data, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        for filename, file_data in data.items():
            f.write(f"File: {filename}\n")
            f.write(f"PRB: {file_data['prb']}\n")
            f.write("MOD List (name, x, y):\n")
            for mod in file_data["mod"]:
                f.write(f"  - {mod['name']}: x={mod['x']}, y={mod['y']}\n")
            f.write("WAF die grid coords:\n")
            for cr in file_data.get("waf", []):
                f.write(f"  - {cr}\n")
            # brief wafer summary
            w = file_data.get("wafer", {})
            f.write("Wafer summary:\n")
            f.write(f"  - stepX_um={w.get('stepX_um')}, stepY_um={w.get('stepY_um')}, flat={w.get('flatLocation')} ({w.get('flatAngle_deg')}°)\n")
            f.write(f"  - alignDie={w.get('alignDie')}, alignModule={w.get('alignModule')}, alignModuleXY_um={w.get('alignModuleXY_um')}\n")
            f.write(f"  - centerDie={w.get('centerDie')}\n")
            f.write("\n")
    print(f"Data saved to {output_file} in text format.")

# -------- paths / main --------
dietest_folder   = r"X:\etestonline\DIETEST"
wafer_folder     = r"X:\etestonline\WAFER"
die_folder       = r"X:\etestonline\DIE"
wafertest_folder = r"X:\etestonline\WAFERTEST"

output_json = r"Y:\usr\aquq\etest_app\output.json"
output_text = r"Y:\usr\aquq\etest_app\output.txt"

if os.path.exists(output_json):
    with open(output_json, 'r', encoding='utf-8') as f:
        existing_data = json.load(f)
else:
    existing_data = {}

data = process_folder(dietest_folder, wafer_folder, die_folder, wafertest_folder, existing_data)
save_data_to_json(data, output_json)
save_data_to_text(data, output_text)
