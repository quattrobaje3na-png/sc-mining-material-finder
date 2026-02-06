import requests
import json
import os

URL = "https://api.regolith.rocks"
TOKEN = os.environ.get("REGOLITH_TOKEN")

VERIFIED_SIGS = {
    "ITYPE": 4000, "CTYPE": 4700, "STYPE": 4720, 
    "PTYPE": 4750, "MTYPE": 4850, "QTYPE": 4870, "ETYPE": 4900
}

def sync():
    if not TOKEN:
        print("!! FAIL: REGOLITH_TOKEN missing !!")
        return

    headers = {"x-api-key": TOKEN.strip(), "Content-Type": "application/json"}
    
    # STEP 1: PROBE THE SCHEMA
    print("Probing 'scoutingFind' fields...")
    probe_query = "{ __type(name: \"ScoutingFind\") { fields { name } } }"
    try:
        probe_resp = requests.post(URL, headers=headers, json={"query": probe_query}, timeout=20)
        fields = [f['name'] for f in probe_resp.json().get('data', {}).get('__type', {}).get('fields', [])]
        print(f"AVAILABLE FIELDS ON ScoutingFind: {', '.join(fields)}")
        
        if not fields:
            print("!! SCHEMA PROBE FAILED: Field list is empty !!")
            return

        # STEP 2: BUILD DYNAMIC QUERY
        # We'll use 'id' if it exists, otherwise we'll pick the first likely name field
        name_field = next((f for f in fields if f in ['id', 'name', 'label', 'location', 'dataName']), fields[0])
        data_field = next((f for f in fields if f in ['data', 'content', 'payload']), None)

        if not data_field:
            print(f"!! ERROR: No recognizable data field found in: {fields} !!")
            return

        print(f"Executing dynamic query using {name_field} and {data_field}...")
        main_query = f"query {{ scoutingFind {{ {name_field} {data_field} }} }}"
        
        response = requests.post(URL, headers=headers, json={"query": main_query}, timeout=20)
        result = response.json()
        
        raw_entries = result.get("data", {}).get("scoutingFind", [])
        if not raw_entries:
            print("!! FAIL: scoutingFind returned no data entries !!")
            return

        print(f"SUCCESS: Captured {len(raw_entries)} entries. Mapping...")

        ore_data = {}
        rock_data = {}

        for entry in raw_entries:
            loc_name = str(entry.get(name_field, "UNKNOWN"))
            content = entry.get(data_field, {})
            
            if isinstance(content, str):
                try: content = json.loads(content)
                except: content = {}

            # Process Ores
            ore_list = content.get("ores", [])
            ore_data[loc_name] = {
                "ores": {o["name"].capitalize(): o["prob"] for o in ore_list if "name" in o}
            }

            # Process Rock Signatures
            is_p = not any(k in loc_name.upper() for k in ['HALO', 'BELT', 'L1', 'L2', 'L3', 'L4', 'L5'])
            rock_types = content.get("rockTypes", [])
            
            rock_data[loc_name] = {
                "is_planetary": is_p,
                "signatures": {"GROUND": 4000, "HAND": 3000} if is_p else {
                    rt.get("type", "").upper(): VERIFIED_SIGS.get(rt.get("type", "").upper() + "TYPE", 4870)
                    for rt in rock_types if "type" in rt
                }
            }

        with open("ore_locations.json", "w") as f: json.dump(ore_data, f, indent=2)
        with open("rock.json", "w") as f: json.dump(rock_data, f, indent=2)
        print("Verification: Both files written successfully.")

    except Exception as e:
        print(f"!! CRITICAL ERROR: {str(e)} !!")

if __name__ == "__main__":
    sync()
