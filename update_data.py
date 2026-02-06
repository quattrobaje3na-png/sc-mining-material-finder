import requests
import json
import os

URL = "https://api.regolith.rocks"
TOKEN = os.environ.get("REGOLITH_TOKEN")

# Simple query to test connectivity
QUERY = "query { surveyLocations { id } }"

def sync():
    if not TOKEN:
        print("!! ERROR: REGOLITH_TOKEN is not found in GitHub Secrets !!")
        return

    # Scrubbing the token to ensure no accidental whitespace/newlines
    clean_token = TOKEN.strip().replace('"', '').replace("'", "")
    
    headers = {
        "x-api-key": clean_token,
        "Content-Type": "application/json"
    }
    
    try:
        print(f"DEBUG: Using Token (first 4 chars): {clean_token[:4]}...")
        response = requests.post(URL, headers=headers, json={"query": QUERY}, timeout=20)
        
        print(f"DEBUG: HTTP Status: {response.status_code}")
        
        # If the status is 401 or 403, the key is definitely the problem
        if response.status_code in [401, 403]:
            print("!! AUTHENTICATION FAILED: Regolith rejected your API Key !!")
            print(f"API Response: {response.text}")
            return

        data = response.json()
        if "errors" in data:
            print(f"!! API ERROR: {data['errors'][0]['message']} !!")
            return

        locs = data.get("data", {}).get("surveyLocations")
        if locs:
            print(f"SUCCESS: Connected! Found {len(locs)} locations.")
            # ... (Rest of your processing logic here)
        else:
            print("!! EMPTY DATA: The key is valid, but has no access to survey data !!")

    except Exception as e:
        print(f"!! CONNECTION ERROR: {str(e)} !!")

if __name__ == "__main__":
    sync()
