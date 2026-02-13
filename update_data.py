import requests
import json
import os

URL = "https://api.regolith.rocks"
TOKEN = os.environ.get("REGOLITH_TOKEN")

# Reverting to scoutingFind as the collection name, which contains the SurveyData blobs
QUERY = """
query {
  scoutingFind {
    dataName
    epoch
    data
  }
}
"""

def sync():
    if not TOKEN:
        print("!! CRITICAL: REGOLITH_TOKEN secret missing !!")
        return

    headers = {
        "x-api-key": TOKEN.strip(),
        "Content-Type": "application/json"
    }
    
    try:
        print("Fetching Epoch 4.4 Data from Scouting Collection...")
        response = requests.post(URL, json={"query": QUERY}, headers=headers, timeout=20)
        response.raise_for_status()
        result = response.json()

        if "errors" in result:
            print(f"API ERROR: {result['errors'][0]['message']}")
            return

        # Regolith stores survey distributions within the scoutingFind array
        raw_entries = result.get("data", {}).get("scoutingFind", [])
        
        target_epoch = "4.4"
        ore_output = {}

        for entry in raw_entries:
            # Filter specifically for the current Nyx epoch
            if str(entry.get("epoch")) != target_epoch:
                continue

            loc_name = entry.get("dataName") or "UNKNOWN_LOC"
            content = entry.get("data", {})
            
            if isinstance(content, str):
                try: 
                    content = json.loads(content)
                except json.JSONDecodeError: 
                    content = {}

            ores = content.get("ores", [])
            if ores:
                # Format for the Mining Material Finder UI
                ore_output[loc_name] = {
                    "ores": {o["name"].capitalize(): o["prob"] for o in ores if "name" in o},
                    "epoch": target_epoch
                }

        with open("rock_live.json", "w") as f:
            json.dump(ore_output, f, indent=2)
            
        print(f"SUCCESS: Updated rock_live.json with {len(ore_output)} locations for 4.4.")

    except Exception as e:
        print(f"!! FATAL ERROR: {str(e)} !!")

if __name__ == "__main__":
    sync()
