import os
import requests
from mastodon import Mastodon

# --- Load secrets from environment variables ---
PETFINDER_KEY = os.getenv("PETFINDER_KEY")
PETFINDER_SECRET = os.getenv("PETFINDER_SECRET")
MASTODON_BASE_URL = os.getenv("MASTODON_BASE_URL")
MASTODON_ACCESS_TOKEN = os.getenv("MASTODON_ACCESS_TOKEN")

# --- Step 1: Get Petfinder API access token ---
def get_petfinder_token():
    auth_resp = requests.post(
        "https://api.petfinder.com/v2/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": PETFINDER_KEY,
            "client_secret": PETFINDER_SECRET,
        },
    )

    if not auth_resp.ok:
        print("❌ Auth error:", auth_resp.status_code, auth_resp.text)
    auth_resp.raise_for_status()

    return auth_resp.json()["access_token"]

# --- Step 2: Fetch a random pet near 02119 within 10 miles ---
def get_random_pet(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "type": "Cat,Dog",
        "limit": 1,
        "sort": "random",
        "location": "02119",
        "distance": 10,
    }
    resp = requests.get(
        "https://api.petfinder.com/v2/animals",
        headers=headers,
        params=params,
    )

    if not resp.ok:
        print("❌ Pet fetch error:", resp.status_code, resp.text)
    resp.raise_for_status()

    animals = resp.json().get("animals", [])
    return animals[0] if animals else None

# --- Step 3: Post to Mastodon ---
def post_to_mastodon(pet):
    if not pet:
        print("No pet found for given filters.")
        return

    name = pet.get("name", "Unnamed friend")

    # Strip ?referrer_id (or any other query params) from Petfinder URL
    raw_url = pet.get("url", "")
    clean_url = ra_
