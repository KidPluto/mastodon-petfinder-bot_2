import os
import requests
from mastodon import Mastodon
import json
from datetime import datetime, timedelta
import random

# --- Load secrets from environment variables ---
PETFINDER_KEY = os.getenv("PETFINDER_KEY")
PETFINDER_SECRET = os.getenv("PETFINDER_SECRET")
MASTODON_BASE_URL = os.getenv("MASTODON_BASE_URL")
MASTODON_ACCESS_TOKEN = os.getenv("MASTODON_ACCESS_TOKEN")
POSTED_CATS_FILE = 'posted_cats.json'

# ... existing code ...

def load_posted_cats():
    if os.path.exists(POSTED_CATS_FILE):
        with open(POSTED_CATS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_posted_cats(posted_cats):
    with open(POSTED_CATS_FILE, 'w') as f:
        json.dump(posted_cats, f)

def get_recent_cat_ids(posted_cats, days=7):
    cutoff = datetime.utcnow() - timedelta(days=days)
    return {entry['id'] for entry in posted_cats if datetime.fromisoformat(entry['date']) > cutoff}

# --- NEW: Prune entries older than 7 days ---
def prune_posted_cats(posted_cats, days=7):
    cutoff = datetime.utcnow() - timedelta(days=days)
    return [entry for entry in posted_cats if datetime.fromisoformat(entry['date']) > cutoff]

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
    return auth_resp.json().get("access_token")

# --- Step 2: Fetch a random pet near 02119 within 10 miles ---
def get_random_pet(access_token):
    pass

# --- Step 2: Fetch up to 10 random cats near 02119 within 10 miles ---
def get_random_cats(access_token, limit=10):
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "type": "Cat",
        "limit": limit,
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
    return resp.json().get("animals", [])

# --- Step 3: Generate alt text for accessibility ---
def generate_alt_text(pet):
    name = pet.get("name", "Unnamed friend")
    pet_type = pet.get("type", "Pet")
    breeds = pet.get("breeds", {})
    breed = breeds.get("primary") or breeds.get("secondary") or "mixed breed"
    age = pet.get("age", "").lower()
    gender = pet.get("gender", "").lower()
    parts = [name, pet_type.lower(), breed.lower()]
    if age:
        parts.append(age)
    if gender:
        parts.append(gender)
    return "Photo of " + " ".join(parts)

# --- Step 4: Post to Mastodon ---
def post_to_mastodon(pet):
    if not pet:
        print("No pet found for given filters.")
        return

    # Random cat-related icon
    cat_icons = ["🐾", "🐱", "😺", "🐈", "🐈‍⬛", "😸", "😻", "😽", "😼", "🧶"]
    icon = random.choice(cat_icons)

    name = pet.get("name", "Unnamed friend")

    # Strip ?referrer_id (or any other query params) from Petfinder URL
    raw_url = pet.get("url", "")
    clean_url = raw_url.split("?")[0] if raw_url else ""

    description = f"Meet {name}! {icon} Available for adoption in/near Boston.\n{clean_url}"

    mastodon = Mastodon(
        access_token=MASTODON_ACCESS_TOKEN,
        api_base_url=MASTODON_BASE_URL,
    )

    media_ids = []
    photos = pet.get("photos", [])
    if photos:
        img_url = photos[0].get("large") or photos[0].get("medium") or photos[0].get("small")
        if img_url:
            img_data = requests.get(img_url)
            img_data.raise_for_status()
            with open("temp.jpg", "wb") as f:
                f.write(img_data.content)
            alt_text = generate_alt_text(pet)
            media = mastodon.media_post("temp.jpg", "image/jpeg", description=alt_text)
            media_ids.append(media["id"])
            print(f"✅ Uploaded photo with alt text: {alt_text}")

    mastodon.status_post(description, media_ids=media_ids)
    print(f"✅ Posted: {description}")

if __name__ == "__main__":
    token = get_petfinder_token()
    posted_cats = load_posted_cats()
    recent_cat_ids = get_recent_cat_ids(posted_cats)

    # Fetch up to 10 cats to find one not posted recently
    animals = get_random_cats(token, limit=10)

    pet = None
    for candidate in animals:
        if candidate['id'] not in recent_cat_ids:
            pet = candidate
            break

    if pet:
        post_to_mastodon(pet)
        posted_cats.append({'id': pet['id'], 'date': datetime.utcnow().isoformat()})
        # --- NEW: Prune old entries before saving ---
        posted_cats = prune_posted_cats(posted_cats)
        save_posted_cats(posted_cats)
    else:
        print("No new cats to post from the fetched batch.")
        print("Of the 10 random cats fetched, all had been posted in the last week.")