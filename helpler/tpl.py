import os
import json
import shutil
import glob
from datetime import datetime
import re

# Define paths
json_path = r"Y:\usr\aquq\SPEC_conv\s90\output.json"
tst_folder = r"/etestnew/SPECS/tpprod/tst"
die_folder = r"/etestnew/SPECS/tpprod/die"
wafer_folder = r"/etestnew/SPECS/tpprod/waf"
# tpl_folder = r"E:\ufiles\AQUQ\E-Test\SPECS translation\mod translation\tpl"
tpl_folder = r"/etestnew/SPECS/tpprod/tpl"
type_typ_file = r"/etestnew/SPECS/tpprod/type_typ.txt"
perimeter_perim_file = r"/etestnew/SPECS/tpprod/perimeter_perim.txt"
vlimit_vlim_file = r"/etestnew/SPECS/tpprod/vlimit_vlim.txt"
dtime_time_file = r"/etestnew/SPECS/tpprod/dtime_time.txt"

current_date = datetime.now().strftime('%m/%d/%Y')
current_time = datetime.now().strftime('%H:%M:%S')

# Load JSON data
with open(json_path, 'r') as file:
    devices = json.load(file)

type_typ_map = {}
if os.path.exists(type_typ_file):
    with open(type_typ_file, "r") as f:
        for line in f:
            parts = line.strip().split(":")
            if len(parts) == 2:
                filename, typ_value = parts[0].strip(), parts[1].strip()
                type_typ_map[filename] = typ_value

perimeter_perim_map = {}
if os.path.exists(perimeter_perim_file):
    with open(perimeter_perim_file, "r") as f:
        for line in f:
            parts = line.strip().split(":")
            if len(parts) == 2:
                filename, typ_value = parts[0].strip(), parts[1].strip()
                perimeter_perim_map[filename] = typ_value

vlimit_vlim_map = {}
if os.path.exists(vlimit_vlim_file):
    with open(vlimit_vlim_file, "r") as f:
        for line in f:
            parts = line.strip().split(":")
            if len(parts) == 2:
                filename, typ_value = parts[0].strip(), parts[1].strip()
                vlimit_vlim_map[filename] = typ_value

dtime_time_map = {}
if os.path.exists(dtime_time_file):
    with open(dtime_time_file, "r") as f:
        for line in f:
            parts = line.strip().split(":")
            if len(parts) == 2:
                filename, typ_value = parts[0].strip(), parts[1].strip()
                dtime_time_map[filename] = typ_value

def fix_tpl_file(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        if "Z_RES4PT_CRE" in line and "RCDDLICONPK" in line and "Cts=" in line:
            line = re.sub(r'\bCts\s*=', 'Sq =', line)
        if "Z_LINEW4PT_CRE" in line and "RSCAP2MH_2p0" in line and "Length=" in line:
            line = re.sub(r'\bLength\s*=', 'Sq    =', line)
        if "Z_RES2PT_CRE" in line and "RSLNLI" in line and "Length=" in line:
            line = re.sub(r'\bLength\s*=', 'Sq    =', line)
        new_lines.append(line)

    with open(filepath, 'w', newline='\n') as f:
        f.writelines(new_lines)
# Function to check mod files
def check_mod_files(mod_list):
    matched_files = []
    for mod in mod_list:
        # For mods starting with "c9fd", allow any last character
        if mod.startswith("c9fd"):
            search_pattern = os.path.join(tst_folder, f"{mod[:-1]}?.tst")
            matched = glob.glob(search_pattern)
            if matched:
                matched_files.extend(matched)
            else:
                # print(mod)
                return False, []
        else:
            mod_path = os.path.join(tst_folder, f"{mod}.tst")
            if os.path.exists(mod_path):
                matched_files.append(mod_path)
            else:
                print(mod)
                return False, []
    return True, matched_files

# Iterate over each device in JSON
for device_name, device_info in devices.items():
    mods = device_info.get("mod", [])
    prb = device_info.get("prb", "")

    if not mods:
        print(f"Skipping device {device_name}: mod list is empty.")
        continue
    
    # Check for mod files
    mods_exist, mod_files = check_mod_files(mods)
    if not mods_exist:
        print(f"Skipping device {device_name}: not all mods exist.")
        continue

    # Check for die and wafer files
    die_path = os.path.join(die_folder, f"{device_name}.die")
    wafer_path = os.path.join(wafer_folder, f"{device_name}.waf")

    if not os.path.exists(die_path):
        print(f"Skipping device {device_name}: die file is missing.")
        continue
    if not os.path.exists(wafer_path):
        print(f"Skipping device {device_name}: wafer file is missing.")
        continue

    # Create output file in tpl folder
    tpl_path = os.path.join(tpl_folder, f"{device_name}.tpl")
    with open(tpl_path, 'w', newline='\n') as tpl_file:
        # Copy wafer file

        begin_section = f"""#Test Plan	{device_name}	1	{current_date}	{current_time} specs	
#Library	measure/SKT_MEASURE	1	{current_date}	{current_time} specs	
#Library	tester/HP4062UX	1	{current_date}	{current_time} specs	TSTR:Agilent 4062UX Tester Algorithms
#Library	prober/EG4080_HPSTD	1	{current_date}	{current_time} specs	PRBR:EG4080 Prober Algorithms (Enhanced)
#Library	utility/UTILITY4062	1	{current_date}	{current_time} specs	UTIL:Utility Algorithms
#Wafer	{device_name}	1	{current_date}	{current_time} specs	{device_name}	
#Die	{device_name}	1	{current_date}	{current_time} specs	{device_name}	
#Probe	{prb}	1	{current_date}	{current_time}	specs	
#Test	{device_name}	1	{current_date}	{current_time}	specs	
#Job	SYSTEM	1	{current_date}	{current_time}	specs	
""".splitlines()
        begin_section_justified = "\n".join(line for line in begin_section)
        tpl_file.write(begin_section_justified)
        tpl_file.write("\n")
        tpl_file.write('\f\n')
        with open(wafer_path, 'r') as wf:
            shutil.copyfileobj(wf, tpl_file)
        tpl_file.write('\f\n')
        
        # Copy only relevant and **non-duplicate** lines from the die file
        seen_mods = set()  # Track mods already written
        with open(die_path, 'r') as df:
            for line in df:
                if line.strip().startswith("`"):  # Check for mod line
                    mod_name = line.split()[0].strip("`")  # Extract mod name
                    if mod_name in mods and mod_name not in seen_mods:
                        tpl_file.write(line)  # Write the filtered line
                        seen_mods.add(mod_name)  # Mark as written
                else:
                    tpl_file.write(line)  # Write non-mod lines
        tpl_file.write('\f\n')

        probe_section = f"""$Type: Probe
$Name: pin12
$Vers: 1
$Desc: 
$Date: 09/09/1991
$Time: 10:13:39
$User: specs
$---- --- ----- - - -----------------
 BODY                                
      PAD 1,14      Pad #1  = Pin #14
      PAD 2,44      Pad #2  = Pin #44
      PAD 3,38      Pad #3  = Pin #38
      PAD 4,37      Pad #4  = Pin #37
      PAD 5,7       Pad #5  = Pin #7 
      PAD 6,5       Pad #6  = Pin #5 
      PAD 7,46      Pad #7  = Pin #46
      PAD 8,47      Pad #8  = Pin #47
      PAD 9,48      Pad #9  = Pin #48
      PAD 10,1      Pad #10 = Pin #1 
      PAD 11,2      Pad #11 = Pin #2 
      PAD 12,3      Pad #12 = Pin #3 
      PAD 36,36     Pad #36 = Pin #36
$---- --- ----- - - -----------------
""".splitlines()


        probe_section_justified = "\n".join(line for line in probe_section)
        tpl_file.write(probe_section_justified)
        tpl_file.write('\n')
        tpl_file.write('\f\n')

        # Copy all mod files and add corresponding TEST line for each
        test_lines = []
        for mod_file in mod_files:
            test_count = {}  # Track occurrences of each test

            with open(mod_file, 'r') as mf:
                for line in mf:
                    if "::" in line:  # Check for test definition
                        updated_line = ""
                        parts = line.split("::")
                        test_full = parts[1].split(":")[0]  # Extract full test section (e.g., "`RESN`")

                        # Extract the actual test name without backticks
                        test_name = test_full.strip("`")

                        if test_name in test_count:
                            test_count[test_name] += 1
                            new_test_name = f"{len(test_name) * ' '}"  # Append _1, _2, etc.
                            modified_line = re.sub(rf"`{test_name}`:", f"{new_test_name}   ", line, count=1)
                        else:
                            test_count[test_name] = 0  # First occurrence stays unchanged
                            new_test_name = f"`{test_name}`"
                            modified_line = line  # No changes needed
                        modified_line = re.sub(r'"""(.*?)"""', r'"\1"    ', modified_line)
                        modified_line = re.sub(r'"""', '"" ', modified_line)

                        # pattern = r"(Time=\S+)(\s{1,})(\S+)"  # Capture spaces in Group 2

                        # # Replace "Time=" with "Dtime=" and remove exactly 1 space
                        # modified_line = re.sub(pattern, lambda m: f"Dtime={m.group(1)[5:]}{m.group(2)[:-1]}{m.group(3)}", modified_line)


                        modified_line = re.sub(r"(\w+)=([^,]*)\"\"", r'\1="\2"', modified_line)
                        modified_line = re.sub(r"Sq\([^\)]*\)=", lambda m: "Sq" + " " * (len(m.group(0)) - 3) + "=", modified_line)
                        # modified_line = re.sub(r",\w+=-(?=\s|,|$)", lambda m: " " * (len(m.group(0)) - 1), modified_line)

                        matches = re.findall(r",\w+=\"-\"(?=\s|,|$)", modified_line)

                        # Step 2: Replace each match with an equivalent number of spaces
                        for match in matches:
                            modified_line = modified_line.replace(match, " " * len(match), 1)

                        for key, replacement in type_typ_map.items():
                            if key in modified_line:
                                updated_line = re.sub(r"(Type|Typ)=", replacement + "=", modified_line)
                                # if key == "Z_IDS1VAL_MOS":
                                    # print(updated_line)

                                spaces_needed = len(modified_line) - len(updated_line)
                                if spaces_needed > 0:
                                    # Ensure space after '=' if missing
                                    updated_line = re.sub(rf"({replacement})=", r"\1 =", updated_line)
                                    updated_line = re.sub(r" (=...)", r"\1 ", updated_line)

                                elif spaces_needed < 0:
                                    # Ensure no extra spaces before '='
                                    updated_line = re.sub(rf"({replacement})\s*=", r"\1=", updated_line)

                                    # Remove exactly one space after `group(1)`
                                    updated_line = re.sub(rf"({replacement}\S*) ", r"\1", updated_line)
                                modified_line = updated_line
                                break
                            
                        for key, replacement in perimeter_perim_map.items():
                            if key in modified_line:
                                updated_line = re.sub(r"(Perimeter|Perim)=", replacement + "=", modified_line)
                                # if key == "Z_IDS1VAL_MOS":
                                    # print(updated_line)

                                spaces_needed = len(modified_line) - len(updated_line)
                                if spaces_needed > 0:
                                    # Ensure space after '=' if missing
                                    # updated_line = re.sub(rf"({replacement})=", rf"({replacement}) =", updated_line)
                                    updated_line = re.sub(rf"({replacement})=([\d.]+)", rf"{replacement}=\2    ", updated_line)

                                elif spaces_needed < 0:
                                    # Ensure no extra spaces before '='
                                    updated_line = re.sub(rf"({replacement})\s*=", r"\1=", updated_line)

                                    # Remove exactly one space after `group(1)`
                                    updated_line = re.sub(r"(=\S) ", r"\1", updated_line)
                                modified_line = updated_line
                                break
                        
                        for key, replacement in vlimit_vlim_map.items():
                            if key in modified_line:
                                updated_line = re.sub(r"(Vlimit|Vlim)=", replacement + "=", modified_line)

                                spaces_needed = len(modified_line) - len(updated_line)
                                if spaces_needed > 0:
                                    # Ensure space after '=' if missing
                                    # updated_line = re.sub(rf"({replacement})=", rf"({replacement}) =", updated_line)
                                    updated_line = re.sub(rf"({replacement})=([\d.]+)", rf"{replacement}=\2 ", updated_line)

                                elif spaces_needed < 0:
                                    pattern = rf"({replacement}=\S+)(\s{{2,}})(\S+)"  # Capture spaces in Group 2

                                    matches = re.findall(pattern, updated_line)
                                    if matches:
                                        print("Matches found:", matches)  # Should show spaces in Group 2

                                    # Perform the replacement, reducing Group 2 by exactly 2 characters (spaces)
                                    updated_line = re.sub(pattern, lambda m: f"{m.group(1)}{m.group(2)[:-2]}{m.group(3)}", updated_line)
                                modified_line = updated_line
                                break

                        for key, replacement in dtime_time_map.items():
                            if key in modified_line:
                                updated_line = re.sub(r"(Dtime|Time)=", replacement + "=", modified_line)

                                spaces_needed = len(modified_line) - len(updated_line)
                                if spaces_needed > 0:
                                    # Ensure space after '=' if missing
                                    # updated_line = re.sub(rf"({replacement})=", rf"({replacement}) =", updated_line)
                                    updated_line = re.sub(rf"({replacement})=([\d.]+)", rf"{replacement}=\2 ", updated_line)

                                elif spaces_needed < 0:
                                    pattern = rf"({replacement}=\S+)(\s{{1,}})(\S+)"  # Capture spaces in Group 2

                                    matches = re.findall(pattern, updated_line)
                                    if matches:
                                        print("Matches found:", matches)  # Should show spaces in Group 2

                                    # Perform the replacement, reducing Group 2 by exactly 2 characters (spaces)
                                    updated_line = re.sub(pattern, lambda m: f"{m.group(1)}{m.group(2)[:-1]}{m.group(3)}", updated_line)
                                modified_line = updated_line
                                break

                        if updated_line:
                            updated_line = re.sub(r'(?i)\btype(?=\s*=\s*)', 'Type', updated_line)
                            updated_line = re.sub(r'(?i)\bdivider\b', 'Devider', updated_line)
                            tpl_file.write(updated_line)
                        else:
                            modified_line = re.sub(r'(?i)\btype(?=\s*=\s*)', 'Type', modified_line)
                            modified_line = re.sub(r'(?i)\bdivider\b', 'Devider', modified_line)
                            tpl_file.write(modified_line)
                    else:
                        tpl_file.write(line)  # Write unchanged lines

                tpl_file.write("\f\n")  # Add form feed at end of each mod file
            
            # Extract filename for TEST line
            mod_file_name = os.path.basename(mod_file)
            test_line = f'      TEST         "{device_name}","{mod_file_name.split(".")[0]}"'
            test_lines.append(test_line)

# Define the header and body sections separately for clarity
        final_section_head = f"""$Type: Job
$Name: SYSTEM
$Vers: 1
$Desc: 
$Date: {current_date}
$Time: {current_time}
$User: specs
$---- ------------ ------------------------------------------------------------ --------- - -
""".splitlines()

        final_section_body = f""" BODY                                                                                        
#     Warning:     Don't change any statements between BEGIN_NAVI and END_NAVI.              
#     BEGIN_NAVI                                                                             
#     SELECT_WAFER {device_name}                                                             
#     SELECT_PROBE pin12                                                                     
#     SELECT_DIE   {device_name}                                                             
#     SELECT_TEST  {device_name}                                                             
#     DIE_TEST     {device_name}                
#     END_NAVI                                                                               
      SELECT       WAFER,"{device_name}"                                                     
      SELECT       PROBE,"pin12"                                                             
""".splitlines()

# Write the header, ensuring each line is 120 characters wide for alignment
        final_section_head_justified = "\n".join(line for line in final_section_head)

        # Write the body, also ensuring each line is 120 characters wide for alignment
        final_section_body_justified = "\n".join(line.ljust(93) for line in final_section_body)

        final_section_test_justified = "\n".join(line.ljust(93) for line in test_lines)
        # print(final_section_test_justified)

        # Write the head and body sections to the tpl file
        tpl_file.write(final_section_head_justified)
        tpl_file.write("\n")
        tpl_file.write(final_section_body_justified)
        tpl_file.write("\n")
        tpl_file.write(final_section_test_justified)
        tpl_file.write("\n")

        # Write each generated TEST line for each mod file
        # for line in test_lines:
        #     tpl_file.write(line.ljust(93))


        # Finish the final section with left-justified LOOP and separator
        tpl_file.write("""      LOOP                                                                                   
$---- ------------ ------------------------------------------------------------ --------- - -
\f
""".ljust(180))


    print(f"Created {tpl_path} successfully.")
    fix_tpl_file(tpl_path)
