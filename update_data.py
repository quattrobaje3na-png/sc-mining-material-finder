import requests
import json
import os

URL = "https://api.regolith.rocks"
TOKEN = os.environ.get("REGOLITH_TOKEN")

# YOUR VERIFIED SIGNATURES
VERIFIED_SIGNATURES = {
    "ITYPE": 4000, "CTYPE": 4700, "STYPE": 4720, 
    "PTYPE": 4750, "MTYPE": 4850, "QTYPE": 4870, "ETYPE": 4900
}

# UPDATED QUERY: Using 'surveyData' as suggested by the API error
QUERY = """
query {
  surveyData {
    id
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
        print("Contacting Regolith API (Targeting surveyData)...")
        response = requests.post(URL, headers=headers, json={"query": QUERY}, timeout=20)
        
        if response.status_code != 200:
            print(f"Status {response.status_code}: {response.text[:200]}")
            return

        data = response.json()
        if "errors" in data:
            print(f"API ERROR: {data['errors'][0]['message']}")
            return

        # Access the new surveyData field
        raw_locs = data.get("data", {}).get("surveyData", [])
        if not raw_locs:
            print("!! FAIL: surveyData returned empty. Verify API permissions !!")
            return

        print(f"SUCCESS: Captured {len(raw_locs)} locations!")

        # STAGE 1: Process and Write ore_locations.json
        ore_data = {}
        for l in raw_locs:
            ore_data[l["id"]] = {
                "ores": {o["name"].capitalize(): o["prob"] for o in l.get("ores", [])}
            }
        with open("ore_locations.json", "w") as f:
            json.dump(ore_data, f, indent=2)

        # STAGE 2: Process and Write rock.json
        rock_data = {}
        for l in raw_locs:
            # Detect moons/planets vs space
            is_planet = not any(k in l["id"].upper() for k in ['HALO', 'BELT', 'RING', 'L1', 'L2', 'L3', 'L4', 'L5'])
            
            rock_data[l["id"]] = {
                "is_planetary": is_planet,
                "signatures": {}
            }
            
            if is_planet:
                rock_data[l["id"]]["signatures"] = {"GROUND": 4000, "HAND": 3000}
            else:
                for rt in l.get("rockTypes", []):
                    rtype = rt["type"].upper()
                    lookup = rtype if rtype.endswith("TYPE") else f"{rtype}TYPE"
                    if lookup in VERIFIED_SIGNATURES:
                        rock_data[l["id"]]["signatures"][rtype] = VERIFIED_SIGNATURES[lookup]

        with open("rock.json", "w") as f:
            json.dump(rock_data, f, indent=2)

        print("Verification: Both files written successfully.")

    except Exception as e:
        print(f"!! CRITICAL ERROR: {str(e)} !!")

if __name__ == "__main__":
    sync()
