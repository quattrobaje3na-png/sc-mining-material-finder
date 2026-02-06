import requests
import json
import os

URL = "https://api.regolith.rocks"
TOKEN = os.environ.get("REGOLITH_TOKEN")

# TARGET QUERY: Switched to 'locationId' based on typical GraphQL naming
QUERY = """
query {
  surveyData {
    locationId
    rockTypes { type prob }
    ores { name prob }
  }
}
"""

def sync():
    if not TOKEN:
        print("!! FAIL: REGOLITH_TOKEN secret missing !!")
        return

    headers = {"x-api-key": TOKEN.strip(), "Content-Type": "application/json"}
    
    try:
        print("Contacting Regolith API (Attempting locationId)...")
        response = requests.post(URL, headers=headers, json={"query": QUERY}, timeout=20)
        data = response.json()

        if "errors" in data:
            error_msg = data['errors'][0]['message']
            print(f"SCHEMA ERROR: {error_msg}")
            
            # AUTO-DISCOVERY: If the query fails, ask the API what fields IT has
            print("Initiating Auto-Discovery of surveyData fields...")
            schema_query = "{ __type(name: \"SurveyData\") { fields { name } } }"
            schema_resp = requests.post(URL, headers=headers, json={"query": schema_query})
            schema_data = schema_resp.json()
            fields = [f['name'] for f in schema_data.get('data', {}).get('__type', {}).get('fields', [])]
            print(f"AVAILABLE FIELDS ON SurveyData: {', '.join(fields)}")
            return

        raw_locs = data.get("data", {}).get("surveyData", [])
        if not raw_locs:
            print("!! FAIL: surveyData returned empty !!")
            return

        print(f"SUCCESS: Captured {len(raw_locs)} locations!")

        # Process and save (using locationId as the key)
        ore_data = {}
        rock_data = {}
        for l in raw_locs:
            lid = l.get("locationId", "UNKNOWN")
            ore_data[lid] = {"ores": {o["name"].capitalize(): o["prob"] for o in l.get("ores", [])}}
            
            is_p = not any(k in lid.upper() for k in ['HALO', 'BELT', 'L1', 'L2', 'L3', 'L4', 'L5'])
            rock_data[lid] = {
                "is_planetary": is_p,
                "signatures": {"GROUND": 4000, "HAND": 3000} if is_p else {
                    rt["type"].upper(): 4870 for rt in l.get("rockTypes", [])
                }
            }

        with open("ore_locations.json", "w") as f: json.dump(ore_data, f, indent=2)
        with open("rock.json", "w") as f: json.dump(rock_data, f, indent=2)
        print("Verification: Both files written successfully.")

    except Exception as e:
        print(f"!! CRITICAL ERROR: {str(e)} !!")

if __name__ == "__main__":
    sync()
