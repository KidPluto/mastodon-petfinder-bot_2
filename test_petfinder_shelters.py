import os
import requests

PETFINDER_KEY = os.getenv("PETFINDER_KEY")
PETFINDER_SECRET = os.getenv("PETFINDER_SECRET")

# Step 1: Get access token
auth_resp = requests.post(
    "https://api.petfinder.com/v2/oauth2/token",
    data={
        "grant_type": "client_credentials",
        "client_id": PETFINDER_KEY,
        "client_secret": PETFINDER_SECRET,
    },
)
auth_resp.raise_for_status()
access_token = auth_resp.json()["access_token"]

# Step 2: Query organizations that have cats near 02119 within 10 miles
headers = {"Authorization": f"Bearer {access_token}"}
params = {
    "location": "02119",
    "distance": 10,
    "type": "Cat",
    "limit": 100,
}

orgs_resp = requests.get(
    "https://api.petfinder.com/v2/organizations",
    headers=headers,
    params=params,
)
orgs_resp.raise_for_status()
orgs = orgs_resp.json().get("organizations", [])

print(f"✅ Found {len(orgs)} shelters with cats available within 10 miles of 02119.")
