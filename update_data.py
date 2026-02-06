import requests
import json
import os

URL = "https://api.regolith.rocks"
TOKEN = os.environ.get("REGOLITH_TOKEN")

VERIFIED_SIGS = {
    "ITYPE": 4000, "CTYPE": 4700, "STYPE": 4720, 
    "PTYPE": 4750, "MTYPE": 4850, "QTYPE": 4870, "ETYPE": 4900
}

# We are testing the 'List' versions of the field since 'surveyData' is now a single-item lookup
QUERIES = [
    "query { allSurveyData { dataName data } }",
    "query { surveyDataList { dataName data } }",
    "query { surveyDataCollection { dataName data } }"
]

def sync():
    if not TOKEN:
        print("!! FAIL: REGOLITH_TOKEN missing !!")
        return

    headers = {"x-api-key": TOKEN.strip(), "Content-Type": "application/json"}
    
    for query in QUERIES:
        try:
            print(f"Attempting Global Query: {query[:30]}...")
            response = requests.post(URL, headers=headers, json={"query": query}, timeout=20)
            result = response.json()

            if "errors" not in result:
                # Find the field name used in the response
                field_name = list(result.get("data", {}).keys())[0]
                raw_entries = result["data"][field_name]
                print(f"SUCCESS: Found {len(raw_entries)} entries via {field_name}!")
                process_and_save(raw_entries)
                return

        except:
            continue

    # SCHEMA DISCOVERY: If all fails, ask the root Query object for its fields
    print("Initiating Root Query Discovery...")
    discovery_query = "{ __type(name: \"Query\") { fields { name } } }"
    disc_resp = requests.post(URL, headers=headers, json={"query": discovery_query})
    fields = [f['name'] for f in disc_resp.json().get('data', {}).get('__type', {}).get('fields', [])]
    print(f"AVAILABLE ROOT FIELDS: {', '.join(fields)}")

def process_and_save(raw_entries):
    ore_data = {}
    rock_data = {}
    for entry in raw_entries:
        loc_name = entry.get("dataName", "UNKNOWN")
        content = entry.get("data", {})
        if isinstance(content, str): content = json.loads(content)

        ore_data[loc_name] = {"ores": {o["name"].capitalize(): o["prob"] for o in content.get("ores", [])}}
        is_p = not any(k in loc_name.upper() for k in ['HALO', 'BELT', 'L1', 'L2', 'L3', 'L4', 'L5'])
        rock_data[loc_name] = {
            "is_planetary": is_p,
            "signatures": {"GROUND": 4000, "HAND": 3000} if is_p else {
                rt.get("type", "").upper(): VERIFIED_SIGS.get(rt.get("type", "").upper() + "TYPE", 4870)
                for rt in content.get("rockTypes", [])
            }
        }
    with open("ore_locations.json", "w") as f: json.dump(ore_data, f, indent=2)
    with open("rock.json", "w") as f: json.dump(rock_data, f, indent=2)
    print("Files successfully updated.")

if __name__ == "__main__":
    sync()
