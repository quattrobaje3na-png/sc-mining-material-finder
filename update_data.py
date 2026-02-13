import requests
import json
import os

URL = "https://api.regolith.rocks"
TOKEN = os.environ.get("REGOLITH_TOKEN")

# Target Query: Pulling SurveyData for the current epoch
QUERY = """
query {
  surveyFind {
    dataName
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
        print("Fetching Epoch 4.4 Survey Data...")
        response = requests.post(URL, json={"query": QUERY}, headers=headers, timeout=20)
        response.raise_for_status()
        result = response.json()

        if "errors" in result:
            print(f"API ERROR: {result['errors'][0]['message']}")
            return

        raw_entries = result.get("data", {}).get("surveyFind", [])
        
        # Filtering for the current epoch (4.4)
        target_epoch = "4.4"
        ore_output = {}

        for entry in raw_entries:
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
                # Capitalizing names for the UI (e.g., 'Laranite', 'Savrilium')
                ore_output[loc_name] = {
                    "ores": {o["name"].capitalize(): o["prob"] for o in ores if "name" in o},
                    "epoch": target_epoch
                }

        # Saving specifically to rock_live.json as requested
        with open("rock_live.json", "w") as f:
            json.dump(ore_output, f, indent=2)
            
        print(f"SUCCESS: Updated rock_live.json with {len(ore_output)} locations.")

    except Exception as e:
        print(f"!! FATAL ERROR: {str(e)} !!")

if __name__ == "__main__":
    sync()
