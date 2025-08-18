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
    auth_resp.raise_for_status()
    return auth_resp.json()["access_token"]

# --- Step 2: Fetch a random pet near 02119 within 10 miles ---
def get_random_pet(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "type": "Cat",
        "limit": 1,
        "sort": "random",
        "location": "02119",   # ZIP filter
        "distance": 10,        # 10 miles
    }
    resp = requests.get(
        "https://api.petfinder.com/v2/animals",
        headers=headers,
        params=params,
    )
    resp.raise_for_status()
    animals = resp.json().get("animals", [])
    return animals[0] if animals else None

# --- Step 3: Post to Mastodon ---
def post_to_mastodon(pet):
    if not pet:
        print("No pet found for given filters.")
        return

    name = pet.get("name", "Unnamed friend")
    url = pet.get("url", "")
    description = f"Meet {name}! 🐾 Available for adoption near Boston (02119).\n{url}"

    mastodon = Mastodon(
        access_token=MASTODON_ACCESS_TOKEN,
        api_base_url=MASTODON_BASE_URL,
    )

    media_ids = []
    photos = pet.get("photos", [])
    if photos:
        img_url = photos[0].get("large") or photos[0].get("medium")
        if img_url:
            img_data = requests.get(img_url)
            img_data.raise_for_status()
            with open("temp.jpg", "wb") as f:
                f.write(img_data.content)
            media = mastodon.media_post("temp.jpg", "image/jpeg")
            media_ids.append(media["id"])

    mastodon.status_post(description, media_ids=media_ids)
    print(f"✅ Posted: {description}")

if __name__ == "__main__":
    token = get_petfinder_token()
    pet = get_random_pet(token)
    post_to_mastodon(pet)
