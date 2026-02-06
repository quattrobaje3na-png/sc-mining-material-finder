import requests
import json
import os

URL = "https://api.regolith.rocks"
TOKEN = os.environ.get("REGOLITH_TOKEN")

# Target Query: Just scoutingFind and the data blob
QUERY = """
query {
  scoutingFind {
    dataName
    data
  }
}
"""

def sync():
    if not TOKEN:
        print("!! CRITICAL: REGOLITH_TOKEN secret missing in GitHub Settings !!")
        return

    headers = {"x-api-key": TOKEN.strip(), "Content-Type": "application/json"}
    
    try:
        print("Authenticating with Regolith...")
        response = requests.post(URL, headers=headers, json={"query": QUERY}, timeout=20)
        result = response.json()

        if "errors" in result:
            print(f"API ERROR: {result['errors'][0]['message']}")
            return

        raw_entries = result.get("data", {}).get("scoutingFind", [])
        if not raw_entries:
            print("!! SUCCESSFUL CONNECTION, BUT NO DATA FOUND !!")
            return

        print(f"SUCCESS: Captured {len(raw_entries)} locations. Processing Ores...")

        ore_output = {}

        for entry in raw_entries:
            # Unpack the JSON blob inside 'data'
            content = entry.get("data", {})
            if isinstance(content, str):
                try: 
                    content = json.loads(content)
                except: 
                    content = {}

            # Use dataName as the primary key (e.g., 'Lyria', 'Wala')
            loc_name = entry.get("dataName") or "UNKNOWN_LOC"
            
            # Extract Ores only
            ores = content.get("ores", [])
            if ores:
                ore_output[loc_name] = {
                    "ores": {o["name"].capitalize(): o["prob"] for o in ores if "name" in o}
                }

        # Save specifically to ore_locations.json
        with open("ore_locations.json", "w") as f:
            json.dump(ore_output, f, indent=2)
            
        print(f"DONE: Updated {len(ore_output)} entries in ore_locations.json.")

    except Exception as e:
        print(f"!! FATAL ERROR: {str(e)} !!")

if __name__ == "__main__":
    sync()
