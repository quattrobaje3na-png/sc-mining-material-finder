import requests
import json
import os

URL = "https://api.regolith.rocks"
TOKEN = os.environ.get("REGOLITH_TOKEN")

# VERIFIED SIGNATURES
VERIFIED_SIGNATURES = {
    "ITYPE": 4000, "CTYPE": 4700, "STYPE": 4720, 
    "PTYPE": 4750, "MTYPE": 4850, "QTYPE": 4870, "ETYPE": 4900
}

# Adjusted Query for the surveyData schema
# Removed 'id' and replaced with 'location' which is more common in this type
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
        print("!! FAIL: REGOLITH_TOKEN is not set in GitHub Secrets !!")
        return

    headers = {"x-api-key": TOKEN.strip(), "Content-Type": "application/json"}
    
    try:
        print("Contacting Regolith API (Deep Scan surveyData)...")
        response = requests.post(URL, headers=headers, json={"query": QUERY}, timeout=20)
        
        data = response.json()
        if "errors" in data:
            error_msg = data['errors'][0]['message']
            print(f"API ERROR: {error_msg}")
            # If 'location' also fails, we'll know immediately from the log
            return

        raw_locs = data.get("data", {}).get("surveyData", [])
        if not raw_locs:
            print("!! FAIL: surveyData returned empty !!")
            return

        print(f"SUCCESS: Captured {len(raw_locs)} locations!")

        ore_data = {}
        rock_data = {}

        for l in raw_locs:
            # Handle the possibility that 'location' is the new ID field
            loc_name = l.get("location", "UNKNOWN_LOC")
            
            # STAGE 1: ORES
            ore_data[loc_name] = {
                "ores": {o["name"].capitalize(): o["prob"] for o in l.get("ores", [])}
            }

            # STAGE 2: ROCKS
            is_planet = not any(k in loc_name.upper() for k in ['HALO', 'BELT', 'RING', 'L1', 'L2', 'L3', 'L4', 'L5'])
            rock_data
