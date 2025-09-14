import os
import requests
from mastodon import Mastodon
import json
from datetime import datetime, timedelta
import logging
import sys
import traceback

# --- Load secrets from environment variables ---
PETFINDER_KEY = os.getenv("PETFINDER_KEY")
PETFINDER_SECRET = os.getenv("PETFINDER_SECRET")
MASTODON_BASE_URL = os.getenv("MASTODON_BASE_URL")
MASTODON_ACCESS_TOKEN = os.getenv("MASTODON_ACCESS_TOKEN")
POSTED_CATS_FILE = 'posted_cats.json'

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("mastodon-petfinder-bot")
logger.info("Starting Mastodon Petfinder Bot")
logger.debug(f"Environment: LOG_LEVEL={LOG_LEVEL}, CWD={os.getcwd()}")

def _redact(value: str, keep_last: int = 4) -> str:
    if not value:
        return "<missing>"
    if len(value) <= keep_last:
        return "*" * len(value)
    return "*" * (len(value) - keep_last) + value[-keep_last:]

# Log environment presence (redacted for secrets)
logger.info(f"Env check: PETFINDER_KEY={_redact(PETFINDER_KEY)} "
            f"PETFINDER_SECRET={_redact(PETFINDER_SECRET)} "
            f"MASTODON_BASE_URL={MASTODON_BASE_URL or '<missing>'} "
            f"MASTODON_ACCESS_TOKEN={_redact(MASTODON_ACCESS_TOKEN)}")
logger.info(f"Posted-cats file path: {os.path.abspath(POSTED_CATS_FILE)}")

# --- Functions to support not repeating posts ---
def load_posted_cats():
    try:
        if os.path.exists(POSTED_CATS_FILE):
            with open(POSTED_CATS_FILE, 'r') as f:
                data = json.load(f)
                logger.info(f"Loaded {len(data)} posted cat entries")
                return data
        logger.info("Posted cats file does not exist yet; starting fresh.")
        return []
    except Exception as e:
        logger.error(f"Failed to load posted cats file: {e}")
        logger.debug("Traceback:\n" + traceback.format_exc())
        return []

def save_posted_cats(posted_cats):
    try:
        with open(POSTED_CATS_FILE, 'w') as f:
            json.dump(posted_cats, f)
        logger.info(f"Saved {len(posted_cats)} posted cat entries")
    except Exception as e:
        logger.error(f"Failed to save posted cats file: {e}")
        logger.debug("Traceback:\n" + traceback.format_exc())

def get_recent_cat_ids(posted_cats, days=7):
    cutoff = datetime.utcnow() - timedelta(days=days)
    recent = {entry['id'] for entry in posted_cats if datetime.fromisoformat(entry['date']) > cutoff}
    logger.info(f"{len(recent)} posted cat IDs within the last {days} days")
    return recent

# --- NEW: Prune entries older than 7 days ---
def prune_posted_cats(posted_cats, days=7):
    cutoff = datetime.utcnow() - timedelta(days=days)
    pruned = [entry for entry in posted_cats if datetime.fromisoformat(entry['date']) > cutoff]
    removed = len(posted_cats) - len(pruned)
    if removed:
        logger.info(f"Pruned {removed} entries older than {days} days")
    else:
        logger.info("No old entries to prune")
    return pruned

# --- Step 1: Get Petfinder API access token ---
def get_petfinder_token():
    logger.info("Requesting Petfinder API token...")
    auth_resp = requests.post(
        "https://api.petfinder.com/v2/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": PETFINDER_KEY,
            "client_secret": PETFINDER_SECRET,
        },
    )
    if not auth_resp.ok:
        logger.error(f"Auth error: {auth_resp.status_code} {auth_resp.text}")
    auth_resp.raise_for_status()
    token = auth_resp.json().get("access_token")
    logger.info("Petfinder token acquired successfully")
    return token

# --- Step 2: Fetch a random pet near 02119 within 10 miles ---
def get_random_pet(access_token):
    # ... existing code ...
    pass
    # ... existing code ...

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
    logger.info(f"Fetching up to {limit} random cats from Petfinder...")
    resp = requests.get(
        "https://api.petfinder.com/v2/animals",
        headers=headers,
        params=params,
    )
    logger.debug(f"Petfinder request URL: {resp.url}")
    if not resp.ok:
        logger.error(f"Pet fetch error: {resp.status_code} {resp.text}")
    resp.raise_for_status()
    animals = resp.json().get("animals", [])
    logger.info(f"Received {len(animals)} animals from Petfinder")
    return animals

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
    alt = "Photo of " + " ".join(parts)
    logger.debug(f"Generated alt text: {alt}")
    return alt

# --- Step 4: Post to Mastodon ---
def post_to_mastodon(pet):
    if not pet:
        logger.warning("No pet found for given filters.")
        return
    pet_id = pet.get("id")
    name = pet.get("name", "Unnamed friend")
    logger.info(f"Preparing to post pet to Mastodon: id={pet_id}, name={name}")

    # Strip ?referrer_id (or any other query params) from Petfinder URL
    raw_url = pet.get("url", "")
    clean_url = raw_url.split("?")[0] if raw_url else ""
    description = f"Meet {name}! 🐾 Available for adoption in/near Boston.\n{clean_url}"
    logger.debug(f"Post description: {description}")

    try:
        mastodon = Mastodon(
            access_token=MASTODON_ACCESS_TOKEN,
            api_base_url=MASTODON_BASE_URL,
        )
        logger.info("Initialized Mastodon client")
    except Exception as e:
        logger.error(f"Failed to initialize Mastodon client: {e}")
        logger.debug("Traceback:\n" + traceback.format_exc())
        raise

    media_ids = []
    photos = pet.get("photos", [])
    if photos:
        img_url = photos[0].get("large") or photos[0].get("medium") or photos[0].get("small")
        logger.info(f"Attempting to upload photo from: {img_url}")
        if img_url:
            try:
                img_data = requests.get(img_url)
                logger.debug(f"Image GET status: {img_data.status_code} url={img_data.url}")
                img_data.raise_for_status()
                with open("temp.jpg", "wb") as f:
                    f.write(img_data.content)
                alt_text = generate_alt_text(pet)
                media = mastodon.media_post("temp.jpg", "image/jpeg", description=alt_text)
                media_ids.append(media["id"])
                logger.info(f"Uploaded photo with alt text. media_id={media['id']}")
            except Exception as e:
                logger.error(f"Failed to upload media: {e}")
                logger.debug("Traceback:\n" + traceback.format_exc())
        else:
            logger.info("No usable image URL found for this pet")
    else:
        logger.info("This pet has no photos; posting text-only status")

    try:
        status = mastodon.status_post(description, media_ids=media_ids)
        status_id = status.get("id")
        logger.info(f"Posted to Mastodon. status_id={status_id}")
    except Exception as e:
        logger.error(f"Failed to post status: {e}")
        logger.debug("Traceback:\n" + traceback.format_exc())
        raise

if __name__ == "__main__":
    try:
        # Validate env early to fail fast in Actions logs
        missing = []
        if not PETFINDER_KEY: missing.append("PETFINDER_KEY")
        if not PETFINDER_SECRET: missing.append("PETFINDER_SECRET")
        if not MASTODON_BASE_URL: missing.append("MASTODON_BASE_URL")
        if not MASTODON_ACCESS_TOKEN: missing.append("MASTODON_ACCESS_TOKEN")
        if missing:
            logger.error(f"Missing required environment variables: {', '.join(missing)}")
            sys.exit(1)

        token = get_petfinder_token()
        posted_cats = load_posted_cats()
        recent_cat_ids = get_recent_cat_ids(posted_cats)

        # --- Fetch up to 10 cats to find one not posted recently ---
        animals = get_random_cats(token, limit=10)
        logger.info("Selecting first animal not posted in the last 7 days...")
        pet = None
        for idx, candidate in enumerate(animals):
            cid = candidate.get('id')
            logger.debug(f"Candidate {idx+1}/{len(animals)}: id={cid} "
                         f"{'(recently posted)' if cid in recent_cat_ids else '(new)'}")
            if cid not in recent_cat_ids:
                pet = candidate
                break

        if pet:
            logger.info(f"Selected pet id={pet.get('id')} name={pet.get('name')}")
            post_to_mastodon(pet)
            posted_cats.append({'id': pet['id'], 'date': datetime.utcnow().isoformat()})
            # --- NEW: Prune old entries before saving ---
            posted_cats = prune_posted_cats(posted_cats)
            save_posted_cats(posted_cats)
            logger.info("Completed run successfully")
        else:
            logger.warning("No new cats to post from the fetched batch.")
            # --- UPDATED: More descriptive message ---
            logger.info("Of the 10 random cats fetched, all had been posted in the last week.")
            logger.info("Consider increasing limit or adjusting filters if this persists.")
    except requests.HTTPError as http_err:
        logger.error(f"HTTP error during run: {http_err}")
        logger.debug("Traceback:\n" + traceback.format_exc())
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during run: {e}")
        logger.debug("Traceback:\n" + traceback.format_exc())
        sys.exit(1)