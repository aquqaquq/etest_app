import json
import os

INPUT_PATH = r'Y:\usr\aquq\etest_app\output.json'
OUTPUT_PATH = r'Y:\usr\aquq\etest_app\output_new.json'

def main():
    # Load input JSON
    with open(INPUT_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("Top-level JSON must be an object mapping device IDs to objects.")

    # Update: set 'mod' to {} for each top-level object that has it
    changed = 0
    for _, obj in data.items():
        if isinstance(obj, dict) and 'mod' in obj:
            obj['mod'] = {}
            changed += 1

    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    # Save result
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Updated {changed} entries. Wrote: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
