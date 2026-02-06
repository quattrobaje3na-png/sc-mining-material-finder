import requests
import json
import os

URL = "https://api.regolith.rocks"
TOKEN = os.environ.get("REGOLITH_TOKEN")

# YOUR VERIFIED SIGNATURE SOURCE OF TRUTH
VERIFIED_SIGNATURES = {
    "ITYPE": 4000, # Ice/Ammonia
    "CTYPE": 4700, # C-type Asteroid
    "STYPE": 4720, # S-type Asteroid
    "PTYPE": 4750, # P-type Asteroid
    "MTYPE": 4850, # M-type Asteroid
    "QTYPE": 4870, # Q-type Asteroid (Quantainium)
    "ETYPE": 4900  # E-type Asteroid (Beryl/Titanium)
}

QUERY = """
query {
  surveyLocations {
    id
    rockTypes {
      type
      prob
    }
    ores {
      name
      prob
    }
  }
}
"""

def sync():
    if not TOKEN:
        print("CRITICAL: REGOLITH_TOKEN is missing from GitHub Secrets.")
        return

    headers = {"x-api-key": TOKEN, "Content-Type": "application/json"}
    payload = {"query": QUERY.replace("\n", " ")}
    
    try:
        print("SCRAPING LIVE DATA & APPLYING VERIFIED SIGNATURES...")
        response = requests.post(URL, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        raw_locations = data.get("data", {}).get("surveyLocations", [])
        master_output = {}

        for loc in raw_locations:
            loc_id = loc["id"]
            master_output[loc_id] = {
                "ores": {},
                "signatures": {}
            }
            
            # 1. Material Probability Mapping
            for ore in loc.get("ores", []):
                name = ore["name"].capitalize()
                if name == "Quantanium": name = "Quantainium"
                master_output[loc_id]["ores"][name] = {"prob": ore["prob"]}
            
            # 2. Rock Type Probability Mapping with Verified Values
            for rt in loc.get("rockTypes", []):
                rtype_raw = rt["type"].upper()
                # Handle single letter or full type strings
                lookup = rtype_raw if rtype_raw.endswith("TYPE") else f"{rtype_raw}TYPE"
                
                if lookup in VERIFIED_SIGNATURES:
                    master_output[loc_id]["signatures"][rtype_raw] = {
                        "sig": VERIFIED_SIGNATURES[lookup],
                        "prob": rt["prob"]
                    }

        # Dropping the cleaned file into your repo
        with open("ore_locations.json", "w") as f:
            json.dump(master_output, f, indent=2)
            
        print(f"SUCCESS: {len(master_output)} locations synced with verified values (Q:4870, E:4900).")

    except Exception as e:
        print(f"SYNC FAILED: {e}")
        exit(1)

if __name__ == "__main__":
    sync()
