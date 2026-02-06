import requests
import json
import os

# API Target
URL = "https://api.regolith.rocks"
TOKEN = os.environ.get("REGOLITH_TOKEN")

# This query pulls every location with its ore probabilities
QUERY = """
query {
  surveyLocations {
    id
    ores {
      name
      prob
    }
  }
}
"""

def sync():
    if not TOKEN:
        print("CRITICAL_ERROR: REGOLITH_TOKEN secret is missing in GitHub Settings.")
        return

    headers = {
        "x-api-key": TOKEN,
        "Content-Type": "application/json"
    }
    
    payload = {"query": QUERY.replace("\n", " ")}
    
    try:
        print("INITIATING SECURE QUANTUM LINK...")
        response = requests.post(URL, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        
        data = response.json()
        
        # Check if the API returned an error message
        if "errors" in data:
            print(f"API_ERROR: {data['errors'][0]['message']}")
            return

        raw_locations = data.get("data", {}).get("surveyLocations", [])
        
        # Transform into the format your tool's scan() function needs
        processed = {}
        for loc in raw_locations:
            loc_id = loc["id"]
            processed[loc_id] = {"ores": {}}
            for ore in loc.get("ores", []):
                # Standardize Quantainium spelling
                name = ore["name"].capitalize()
                if name == "Quantanium": name = "Quantainium"
                processed[loc_id]["ores"][name] = {"prob": ore["prob"]}

        with open("ore_locations.json", "w") as f:
            json.dump(processed, f, indent=2)
            
        print(f"SYNC_COMPLETE: {len(processed)} LOCATIONS UPDATED VIA SECURE LINK.")

    except Exception as e:
        print(f"CONNECTION_FAILURE: {e}")
        exit(1)

if __name__ == "__main__":
    sync()
