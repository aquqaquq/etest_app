import os
import re
from datetime import datetime
import pandas as pd

die_source_folder = r'X:\etestonline\DIE'
wafer_source_folder = r'X:\etestonline\WAFER'
wafertest_source_folder = r'X:\etestonline\WAFERTEST'
EDR = r'E:\ufiles\CACH\Python_Script_Templates\C9_Master_TEST.xlsx'

# waf_folder = r'E:\ufiles\AQUQ\E-Test\SPECS translation\mod translation\waf'
# die_folder = r'E:\ufiles\AQUQ\E-Test\SPECS translation\mod translation\die'

waf_folder = r'Y:\usr\aquq\SPEC_conv\s90\waf'
die_folder = r'Y:\usr\aquq\SPEC_conv\s90\die'

os.makedirs(waf_folder, exist_ok=True)
os.makedirs(die_folder, exist_ok=True)

def extract_data(pattern, text, default_value=""):
    match = re.search(pattern, text)
    return match.group(1).strip() if match else default_value

def create_dynamic_separator_line_waf(max_lengths):
    separator = "$--------- " + " ".join("-" * length for length in max_lengths) + "- - -\n"
    return separator

def create_dynamic_separator_line_die(max_lengths):
    separator = "$---- " + " ".join("-" * length for length in max_lengths) + " - - -------------\n"
    return separator

def parse_die_info(die_content, align_module):
    die_info = {'Align Mod': align_module, 'Align Mod XY': {'X': None, 'Y': None}}
    for line in die_content.splitlines():
        if line.strip().startswith(align_module):
            parts = line.split()
            if len(parts) >= 5:
                die_info['Align Mod XY'] = {'X': float(parts[3]), 'Y': float(parts[4])}
                break
    return die_info

def parse_wafer_info(wafer_content):
    wafer_info = {
        'Die X Step': extract_data(r'Die X Step:\s+(\d+)', wafer_content),
        'Die Y Step': extract_data(r'Die Y Step:\s+(\d+)', wafer_content),
        'Flat Location': extract_data(r'Flat Location \(T,B,L,R\):\s*([TBLR])', wafer_content),
    }
    flat_location_map = {'L': 270, 'R': 90, 'T': 0, 'B': 180}
    wafer_info['Flat Angle'] = flat_location_map.get(wafer_info['Flat Location'], 0)
    reticle_step_size = []
    die_positions_section = wafer_content.split('(table end)')[2].splitlines()
    for line in die_positions_section:
        if re.match(r'^\s*\d', line):
            parts = re.split(r'\s+', line.strip())
            reticle_step_size.append({
                'Column,Row': parts[0],
                'X': parts[2] if len(parts) > 2 else '0',
                'Y': parts[3] if len(parts) > 3 else '0',
                'Die Type': parts[4] if len(parts) > 4 else wafer_info.get('Die Type Name', 'Unknown')
            })
    return wafer_info, reticle_step_size

def parse_wafertest_info(wafertest_content):
    wafertest_info = {
        'WaferType': extract_data(r'WaferType:\s+(.*)', wafertest_content),
        'ProbeCard': extract_data(r'ProbeCard:\s+(.*)', wafertest_content),
        'Align Die': extract_data(r'Align Die:\s+(\d+,\d+)', wafertest_content),
        'Align Module': extract_data(r'Align Module:\s+(.*)', wafertest_content),
    }
    if 'Align Die' in wafertest_info:
        align_die_x, align_die_y = map(int, wafertest_info['Align Die'].split(','))
        wafertest_info['Align Die X'] = align_die_x
        wafertest_info['Align Die Y'] = align_die_y
    return wafertest_info

def find_center_die(column_row_list, wafer_info):
    valid_entries = [cr for cr in column_row_list if ',' in cr]
    if not valid_entries:
        return 0, 0
    x_vals = [int(cr.split(',')[0]) for cr in valid_entries]
    y_vals = [int(cr.split(',')[1]) for cr in valid_entries]
    if (max(x_vals) + min(x_vals)) % 2 == 0 and (max(y_vals) + min(y_vals)) % 2 == 0:
        return (max(x_vals) + min(x_vals)) / 2 , (max(y_vals) + min(y_vals)) / 2, 0, 0
    elif (max(x_vals) + min(x_vals)) % 2 == 0 and (max(y_vals) + min(y_vals)) % 2 != 0:
        return (max(x_vals) + min(x_vals)) / 2 , (max(y_vals) + min(y_vals)) // 2, 0, int(wafer_info['Die Y Step']) / -2
    elif (max(x_vals) + min(x_vals)) % 2 != 0 and (max(y_vals) + min(y_vals)) % 2 == 0:
        return (max(x_vals) + min(x_vals)) // 2 , (max(y_vals) + min(y_vals)) / 2, int(wafer_info['Die X Step']) / -2, 0
    elif (max(x_vals) + min(x_vals)) % 2 != 0 and (max(y_vals) + min(y_vals)) % 2 != 0:
        return (max(x_vals) + min(x_vals)) // 2 , (max(y_vals) + min(y_vals)) // 2, int(wafer_info['Die X Step']) / -2, int(wafer_info['Die Y Step']) / -2
    
def parse_wafer_data(wafer_file, wafertest_file, die_file):
    with open(wafer_file, 'r') as f:
        wafer_content = f.read()
    with open(wafertest_file, 'r') as f:
        wafertest_content = f.read()
    with open(die_file, 'r') as f:
        die_content = f.read()
    wafer_info, reticle_step_size = parse_wafer_info(wafer_content)
    wafertest_info = parse_wafertest_info(wafertest_content)
    align_module = wafertest_info['Align Module']
    die_info = parse_die_info(die_content, align_module)
    column_row_list = [die['Column,Row'] for die in reticle_step_size]
    center_die_x, center_die_y, offset_x, offset_y = find_center_die(column_row_list, wafer_info)
    return {
        'header_info': {
            'Desc': extract_data(r'Desc:\s+(.*)', wafer_content),
            'Creation Date': extract_data(r'Creation Date:\s+(.*)', wafer_content),
            'Revision Date': extract_data(r'Revision Date:\s+(.*)', wafer_content),
        },
        'wafer_info': wafer_info,
        'reticle_step_size': reticle_step_size,
        'die_info': die_info,
        'wafertest_info': wafertest_info,
        'center_die': (center_die_x, center_die_y, offset_x, offset_y),
    }

def calculate_max_lengths_waf(parsed_data):
    max_lengths = [0, 0, 0]
    attributes = [
        "SIZE=REAL,\"mm\"",
        f"STEPX=REAL,\"um\"     {parsed_data['wafer_info']['Die X Step']}.000000",
        f"STEPY=REAL,\"um\"     {parsed_data['wafer_info']['Die Y Step']}.000000",
        f"FLAT=INTEGER,\"deg\"  {parsed_data['wafer_info']['Flat Angle']}",
        f"ALIGNDIEX=INTEGER   {parsed_data['wafertest_info'].get('Align Die X', 0)}",
        f"ALIGNDIEY=INTEGER   {parsed_data['wafertest_info'].get('Align Die Y', 0)}",
        f"ALIGNMODX=REAL,\"um\" {parsed_data['die_info']['Align Mod XY']['X'] or 0.0}",
        f"ALIGNMODY=REAL,\"um\" {parsed_data['die_info']['Align Mod XY']['Y'] or 0.0}",
        f"CENTERDIEX=INTEGER  {parsed_data['center_die'][0] or 0}",
        f"CENTERDIEY=INTEGER  {parsed_data['center_die'][1] or 0}",
        f"OFFSETDIEX=REAL     {parsed_data['center_die'][2] or 0}",
        f"OFFSETDIEY=REAL     {parsed_data['center_die'][3] or 0}",
        f"COORDINATE=INTEGER  1",
        f"WAFERSHAPE=INTEGER  1"
    ]
    for attr in attributes:
        parts = attr.split(maxsplit=2)
        if len(parts) >= 2:
            max_lengths[0] = max(max_lengths[0], len(parts[0]))
            max_lengths[1] = max(max_lengths[1], len(parts[1]))
        if len(parts) == 3:
            max_lengths[2] = max(max_lengths[2], len(parts[2]))
    for die in parsed_data['reticle_step_size']:
        column_row = die['Column,Row']
        die_type = die['Die Type']
        max_lengths[0] = max(max_lengths[0], len(die_type))
        max_lengths[1] = max(max_lengths[1], len(column_row))
    return max_lengths

def calculate_max_lengths_die(die_body_data):
    max_lengths = [0, 0]
    for entry in die_body_data:
        mod_name = entry[0]
        coordinates = entry[1] + ',' + entry[2]
        max_lengths[0] = max(max_lengths[0], len(mod_name))
        max_lengths[1] = max(max_lengths[1], len(coordinates))
    return max_lengths

def generate_waf_file(parsed_data, output_filename):
    current_date = datetime.now().strftime("%m/%d/%Y")
    current_time = datetime.now().strftime("%H:%M:%S")
    align_mod_x = parsed_data['die_info']['Align Mod XY']['X'] or 0.0
    align_mod_y = parsed_data['die_info']['Align Mod XY']['Y'] or 0.0
    flat_angle = parsed_data['wafer_info']['Flat Angle']
    center_die_x = parsed_data['center_die'][0]
    center_die_y = parsed_data['center_die'][1]
    offset_x = parsed_data['center_die'][2]
    offset_y = parsed_data['center_die'][3]
    align_die_x = parsed_data['wafertest_info'].get('Align Die X', 0)
    align_die_y = parsed_data['wafertest_info'].get('Align Die Y', 0)
    max_lengths = calculate_max_lengths_waf(parsed_data)
    separator_line = create_dynamic_separator_line_waf(max_lengths)
    separator_length = len(separator_line.strip())
    waf_content = (
        f"$Type: Wafer\n"
        f"$Name: {output_filename}\n"
        f"$Vers: 1\n"
        f"$Desc: {output_filename}\n"
        f"$Date: {current_date}\n"
        f"$Time: {current_time}\n"
        f"$User: specs\n"
        f"{separator_line.strip()}\n"
        + " ATTRIBUTE".ljust(separator_length) + "\n"
        + "           SIZE=REAL,\"mm\"      200.000000".ljust(separator_length) + "\n"
        + ("           STEPX=REAL,\"um\"     " + f"{parsed_data['wafer_info']['Die X Step']}.000000").ljust(separator_length) + "\n"
        + ("           STEPY=REAL,\"um\"     " + f"{parsed_data['wafer_info']['Die Y Step']}.000000").ljust(separator_length) + "\n"
        + ("           FLAT=INTEGER,\"deg\"  " + f"{flat_angle}").ljust(separator_length) + "\n"
        + ("           ALIGNDIEX=INTEGER   " + f"{align_die_x}").ljust(separator_length) + "\n"
        + ("           ALIGNDIEY=INTEGER   " + f"{align_die_y}").ljust(separator_length) + "\n"
        + ("           ALIGNMODX=REAL,\"um\" " + f"{align_mod_x}").ljust(separator_length) + "\n"
        + ("           ALIGNMODY=REAL,\"um\" " + f"{align_mod_y}").ljust(separator_length) + "\n"
        + ("           CENTERDIEX=INTEGER  " + f"{int(center_die_x)}").ljust(separator_length) + "\n"
        + ("           CENTERDIEY=INTEGER  " + f"{int(center_die_y)}").ljust(separator_length) + "\n"
        + ("           OFFSETDIEX=REAL     " + f"{offset_x}").ljust(separator_length) + "\n"
        + ("           OFFSETDIEY=REAL     " + f"{offset_y}").ljust(separator_length) + "\n"
        + "           COORDINATE=INTEGER  1".ljust(separator_length) + "\n"
        + "           WAFERSHAPE=INTEGER  1".ljust(separator_length) + "\n"
        + " BODY".ljust(separator_length) + "\n"
    )
    for die in parsed_data['reticle_step_size']:
        waf_content += (
            f"           `{die['Die Type']}`".ljust(10 + max_lengths[0] - 1) +
            f"   {die['Column,Row']}".ljust(separator_length - (10 + max_lengths[0]) + 1) + "\n"
        )
    waf_content += separator_line.strip() + "\n"
    waf_file_path = os.path.join(waf_folder, f"{output_filename}.waf")
    with open(waf_file_path, 'w', newline='\n') as waf_file:
        waf_file.write(waf_content)

def generate_die_file(die_file_path, output_filename):
    edr_path = r'E:\ufiles\CACH\Python_Script_Templates\C9_Master_TEST.xlsx'
    df = pd.read_excel(edr_path)
    current_date = datetime.now().strftime("%m/%d/%Y")
    current_time = datetime.now().strftime("%H:%M:%S")
    with open(die_file_path, 'r') as f:
        lines = f.readlines()
    lines = [line for line in lines if "table end" not in line and line.strip()]
    desc = lines[0].split(":")[1].strip()
    die_body_data = []
    start_index = None
    for i, line in enumerate(lines):
        if line.startswith("*"):
            start_index = i + 2
            break
    if start_index is not None:
        for line in lines[start_index:]:
            if line.startswith("*"):
                continue
            parts = line.split()
            if len(parts) >= 5:
                die_body_data.append((parts[0], parts[3], parts[4]))
    max_lengths = calculate_max_lengths_die(die_body_data)
    max_lengths[0] += 2
    separator_line = create_dynamic_separator_line_die(max_lengths)
    separator_length = len(separator_line.strip())
    die_content = (
        f"$Type: Die\n"
        f"$Name: {output_filename}\n"
        f"$Vers: 1\n"
        f"$Desc: {output_filename}\n"
        f"$Date: {current_date}\n"
        f"$Time: {current_time}\n"
        f"$User: specs\n"
        f"{separator_line.strip()}\n"
        f"{' BODY'.ljust(separator_length)}\n"
    )

    no_colon = []
    yes_colon = []
    
    # Categorize entries into no_colon and yes_colon
    for entry in die_body_data:
        module_name = entry[0]
        matching_rows = df[df['MODULE_NAME'] == module_name]
        if not matching_rows.empty:
            has_colon = False
            for _, row in matching_rows.iterrows():
                row_content = ' '.join(row.astype(str).values)
                if ':' in row_content:
                    has_colon = True
                    break
            if has_colon:
                yes_colon.append(entry)
            else:
                no_colon.append(entry)
        else:
            no_colon.append(entry)
    
    # Write no_colon entries first
    for entry in no_colon:
        mod_name = f"`{entry[0]}`".ljust(max_lengths[0])
        coordinates = f"{entry[1]},{entry[2]}".ljust(max_lengths[1] + 1)
        die_content += f"      {mod_name} {coordinates}".ljust(separator_length) + "\n"
    
    # Process yes_colon with dependency ordering
    temp_yes_colon = yes_colon.copy()
    processed = set()  # Track modules already added to avoid duplicates
    
    while temp_yes_colon:
        added_something = False
        for mod in temp_yes_colon[:]:  # Copy to allow modification during iteration
            # Get all rows for this mod
            matching_rows = df[df['MODULE_NAME'] == mod[0]]  # mod is a tuple (name, x, y)
            depends_on_other_mod = False
            
            # Check if this mod depends on any other mod in yes_colon
            for _, row in matching_rows.iterrows():
                row_content = ' '.join(row.astype(str).values)
                for other_mod in yes_colon:
                    if other_mod[0] != mod[0] and other_mod[0] in row_content:  # Compare module names
                        if other_mod not in processed:
                            depends_on_other_mod = True
                            break
                if depends_on_other_mod:
                    break
            
            # If no dependency or all dependencies are already processed, add it
            if not depends_on_other_mod and mod not in processed:
                mod_name = f"`{mod[0]}`".ljust(max_lengths[0])  # Use mod instead of entry
                coordinates = f"{mod[1]},{mod[2]}".ljust(max_lengths[1] + 1)
                die_content += f"      {mod_name} {coordinates}".ljust(separator_length) + "\n"
                processed.add(mod)
                temp_yes_colon.remove(mod)
                added_something = True
        
        # If no progress is made, handle remaining mods
        if not added_something:
            for mod in temp_yes_colon:
                if mod not in processed:
                    mod_name = f"`{mod[0]}`".ljust(max_lengths[0])  # Use mod instead of entry
                    coordinates = f"{mod[1]},{mod[2]}".ljust(max_lengths[1] + 1)
                    die_content += f"      {mod_name} {coordinates}".ljust(separator_length) + "\n"
                    processed.add(mod)
            break

    die_content += separator_line.strip() + "\n"
    
    die_file_path = os.path.join(die_folder, f"{output_filename}.die")
    with open(die_file_path, 'w', newline='\n') as die_file:
        die_file.write(die_content)

def process_files():
    die_files = os.listdir(die_source_folder)
    for die_file in die_files:
        die_file_path = os.path.join(die_source_folder, die_file)
        wafer_file_path = os.path.join(wafer_source_folder, die_file)
        wafertest_file_path = os.path.join(wafertest_source_folder, die_file)
        if os.path.isfile(die_file_path) and os.path.isfile(wafer_file_path) and os.path.isfile(wafertest_file_path):
            print(f"Processing device: {die_file}")
            try:
                parsed_data = parse_wafer_data(wafer_file_path, wafertest_file_path, die_file_path)
                generate_die_file(die_file_path, die_file)
                generate_waf_file(parsed_data, die_file)
            except Exception as e:
                print(f"Error processing device {die_file}: {e}")

process_files()
