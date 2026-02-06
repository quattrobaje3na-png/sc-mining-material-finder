import requests
import json
import os

URL = "https://api.regolith.rocks"
TOKEN = os.environ.get("REGOLITH_TOKEN")

VERIFIED_SIGNATURES = {
    "ITYPE": 4000, "CTYPE": 4700, "STYPE": 4720, 
    "PTYPE": 4750, "MTYPE": 4850, "QTYPE": 4870, "ETYPE": 4900
}

# Primary query attempt
QUERY = """
query {
  surveyData {
    location
    rockTypes { type prob }
    ores { name prob }
  }
}
"""

def sync():
    if not TOKEN:
        print("!! FAIL: REGOLITH_TOKEN is not set !!")
        return

    headers = {"x-api-key": TOKEN.strip(), "Content-Type": "application/json"}
    
    try:
        print("Contacting Regolith API...")
        response = requests.post(URL, headers=headers, json={"query": QUERY}, timeout=20)
        data = response.json()

        # Check for schema errors
        if "errors" in data:
            error_msg = data['errors'][0]['message']
            print(f"API SCHEMA ERROR: {error_msg}")
            return

        raw_locs = data.get("data", {}).get("surveyData", [])
        if not raw_locs:
            print("!! FAIL: surveyData returned empty !!")
            return

        print(f"SUCCESS: Captured {len(raw_locs)} locations!")

        ore_data = {}
        rock_data = {}

        for l in raw_locs:
            loc_name = l.get("location", "UNKNOWN_LOC")
            
            # STAGE 1: ORE DATA
            ore_data[loc_name] = {
                "ores": {o["name"].capitalize(): o["prob"] for o in l.get("ores", [])}
            }

            # STAGE 2: ROCK/SCAN DATA
            is_planet = not any(k in loc_name.upper() for k in ['HALO', 'BELT', 'RING', 'L1', 'L2', 'L3', 'L4', 'L5'])
            rock_data[loc_name] = {
                "is_planetary": is_planet,
                "signatures": {"GROUND": 4000, "HAND": 3000} if is_planet else {
                    rt["type"].upper(): VERIFIED_SIGNATURES.get(rt["type"].upper() + "TYPE", 0) 
                    for rt in l.get("rockTypes", [])
                }
            }

        with open("ore_locations.json", "w") as f:
            json.dump(ore_data, f, indent=2)
        with open("rock.json", "w") as f:
            json.dump(rock_data, f, indent=2)

        print("Verification: Both files written successfully.")

    except Exception as e:
        print(f"!! FATAL SYSTEM ERROR: {str(e)} !!")

if __name__ == "__main__":
    sync()
