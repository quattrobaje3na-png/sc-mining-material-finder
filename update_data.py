import requests
import json
import os

URL = "https://api.regolith.rocks"
TOKEN = os.environ.get("REGOLITH_TOKEN")

# SPACE-ONLY SIGNATURES (Asteroid Belts/Halos)
SPACE_SIGNATURES = {
    "CTYPE": 4700, "STYPE": 4720, "PTYPE": 4750, 
    "MTYPE": 4850, "QTYPE": 4870, "ETYPE": 4900
}

# HELPER: Identify if location is ground or space
def is_planetary(loc_id):
    # Standard asteroid/belt keywords
    space_keywords = ['HALO', 'BELT', 'RING', 'L1', 'L2', 'L3', 'L4', 'L5']
    return not any(k in loc_id.upper() for k in space_keywords)

QUERY = """
query {
  surveyLocations {
    id
    rockTypes { type prob }
    ores { name prob }
  }
}
"""

def sync():
    if not TOKEN:
        print("ERROR: REGOLITH_TOKEN secret missing.")
        return

    headers = {"x-api-key": TOKEN, "Content-Type": "application/json"}
    payload = {"query": QUERY.replace("\n", " ")}
    
    try:
        response = requests.post(URL, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        raw_locations = data.get("data", {}).get("surveyLocations", [])
        master_output = {}

        for loc in raw_locations:
            loc_id = loc["id"]
            planetary = is_planetary(loc_id)
            
            master_output[loc_id] = {
                "ores": {},
                "signatures": {},
                "is_planetary": planetary
            }
            
            for ore in loc.get("ores", []):
                name = ore["name"].capitalize()
                if name == "Quantanium": name = "Quantainium"
                master_output[loc_id]["ores"][name] = {"prob": ore["prob"]}
            
            for rt in loc.get("rockTypes", []):
                rtype_raw = rt["type"].upper()
                lookup = rtype_raw if rtype_raw.endswith("TYPE") else f"{rtype_raw}TYPE"
                
                # Apply logic: If planetary, use unified values. If space, use specific rock types.
                if planetary:
                    master_output[loc_id]["signatures"]["GROUND"] = {"sig": 4000, "type": "Vehicle/Ship"}
                    master_output[loc_id]["signatures"]["HAND"] = {"sig": 3000, "type": "FPS"}
                elif lookup in SPACE_SIGNATURES:
                    master_output[loc_id]["signatures"][rtype_raw] = {
                        "sig": SPACE_SIGNATURES[lookup],
                        "prob": rt["prob"]
                    }

        with open("ore_locations.json", "w") as f:
            json.dump(master_output, f, indent=2)
        print("SYNC SUCCESS: Ground and Space signatures unified.")

    except Exception as e:
        print(f"SYNC FAILED: {e}")
        exit(1)

if __name__ == "__main__":
    sync()
