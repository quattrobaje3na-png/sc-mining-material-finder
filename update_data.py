import requests
import json
import os

URL = "https://api.regolith.rocks"
TOKEN = os.environ.get("REGOLITH_TOKEN")

# Corrected Query: 'dataName' is not a valid field on the ScoutingFind type.
# We use 'id' as the primary identifier for the location.
QUERY = """
query {
  scoutingFind {
    id
    epoch
    data
  }
}
"""

def sync():
    if not TOKEN:
        print("!! CRITICAL: REGOLITH_TOKEN secret missing in GitHub Settings !!")
        return

    headers = {
        "x-api-key": TOKEN.strip(),
        "Content-Type": "application/json"
    }
    
    try:
        print("Connecting to Regolith API for Epoch 4.4 Survey distributions...")
        response = requests.post(URL, json={"query": QUERY}, headers=headers, timeout=20)
        
        # Raise an exception for HTTP errors (401, 403, 500, etc.)
        response.raise_for_status()
        result = response.json()

        if "errors" in result:
            print(f"API ERROR: {result['errors'][0]['message']}")
            return

        raw_entries = result.get("data", {}).get("scoutingFind", [])
        if not raw_entries:
            print("!! CONNECTION SUCCESSFUL, BUT NO DATA FOUND !!")
            return

        # Filtering for the current Nyx epoch (4.4)
        target_epoch = "4.4"
        ore_output = {}

        for entry in raw_entries:
            # Skip entries from older or irrelevant epochs
            if str(entry.get("epoch")) != target_epoch:
                continue

            # 'id' now serves as the location name (e.g., 'Lyria', 'Wala', 'Hades-II')
            loc_name = entry.get("id") or "UNKNOWN_LOC"
            
            # The 'data' field contains the distribution blob
            content = entry.get("data", {})
            if isinstance(content, str):
                try: 
                    content = json.loads(content)
                except json.JSONDecodeError: 
                    content = {}

            # Map the Ores (including new Nyx ores like Savrilium and Torite)
            ores = content.get("ores", [])
            if ores:
                ore_output[loc_name] = {
                    "ores": {o["name"].capitalize(): o["prob"] for o in ores if "name" in o},
                    "epoch": target_epoch
                }

        # Save to rock_live.json for the Mining Material Finder
        with open("rock_live.json", "w") as f:
            json.dump(ore_output, f, indent=2)
            
        print(f"SUCCESS: Updated rock_live.json with {len(ore_output)} locations for 4.4.")

    except Exception as e:
        print(f"!! FATAL ERROR: {str(e)} !!")

if __name__ == "__main__":
    sync()
