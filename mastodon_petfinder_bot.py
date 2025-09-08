#!/usr/bin/env python3
"""
Mastodon Petfinder Bot

Posts a random adoptable Cat from Petfinder (near 02119 within 10 miles) to Mastodon.
- Avoids re-posting the same cat within the last 7 days by tracking IDs in posted_cats.json
- Retries fetching in multiple random batches so we don't give up too early
- Adds a random cat-themed icon to each post (instead of fixed paws)
- Generates alt text for accessibility if an image is uploaded
- Handles intermittent Petfinder failures with simple retry/backoff
"""

import os
import json
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import requests
from mastodon import Mastodon

# ========== Configuration via environment ==========
PETFINDER_KEY = os.getenv("PETFINDER_KEY")
PETFINDER_SECRET = os.getenv("PETFINDER_SECRET")

MASTODON_BASE_URL = os.getenv("MASTODON_BASE_URL")
MASTODON_ACCESS_TOKEN = os.getenv("MASTODON_ACCESS_TOKEN")

# Location settings
PET_LOCATION = os.getenv("PET_LOCATION", "02119")
PET_DISTANCE_MILES = int(os.getenv("PET_DISTANCE_MILES", "10"))

# File to track which cats were posted recently (for de-duplication)
POSTED_CATS_FILE = os.getenv("POSTED_CATS_FILE", "posted_cats.json")

# How many days to remember posted cats (used for pruning and skip logic)
RECENT_DAYS = int(os.getenv("RECENT_DAYS", "7"))

# Network timeouts (seconds)
HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "15"))

# How many random batches to attempt before giving up (helps avoid “no new cats” too early)
MAX_RANDOM_BATCH_ATTEMPTS = int(os.getenv("MAX_RANDOM_BATCH_ATTEMPTS", "6"))

# How many animals to fetch per batch
BATCH_LIMIT = int(os.getenv("BATCH_LIMIT", "50"))

# ========== Random cat-themed icons ==========
# Will choose one per post
CAT_ICONS = [
    "😺", "😸", "😻", "🐱", "🐈", "🐈‍⬛", "🧶", "😼", "😽", "😹", "🐾", "🎀", "🪶"
]

def get_random_cat_icon() -> str:
    return random.choice(CAT_ICONS)

# ========== Local store helpers ==========
def load_posted_cats() -> List[Dict]:
    """
    Load the local JSON file tracking posted cats.
    Returns an empty list if file does not exist or is unreadable.
    """
    if os.path.exists(POSTED_CATS_FILE):
        try:
            with open(POSTED_CATS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception as e:
            print(f"⚠️ Could not read {POSTED_CATS_FILE}: {e}")
    return []

def save_posted_cats(posted_cats: List[Dict]) -> None:
    """
    Persist the posted cats list to disk (ensures file is created).
    """
    try:
        with open(POSTED_CATS_FILE, "w", encoding="utf-8") as f:
            json.dump(posted_cats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Could not write {POSTED_CATS_FILE}: {e}")

def prune_posted_cats(posted_cats: List[Dict], days: int = RECENT_DAYS) -> List[Dict]:
    """
    Keep only entries newer than cutoff days.
    Each entry is expected to be {'id': <int>, 'date': <iso string>}
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    pruned = []
    for entry in posted_cats:
        try:
            when = datetime.fromisoformat(entry.get("date", ""))
            if when > cutoff:
                pruned.append(entry)
        except Exception:
            # If malformed, drop it to keep file clean
            continue
    return pruned

def get_recent_cat_ids(posted_cats: List[Dict], days: int = RECENT_DAYS) -> set:
    """
    Return a set of IDs posted within the last 'days'.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    recent = set()
    for entry in posted_cats:
        try:
            when = datetime.fromisoformat(entry.get("date", ""))
            if when > cutoff:
                recent.add(entry["id"])
        except Exception:
            continue
    return recent

# ========== Petfinder API helpers ==========
def get_petfinder_token(max_retries: int = 3, backoff_base: float = 1.5) -> str:
    """
    Fetches Petfinder API OAuth token with simple retries to handle intermittent failures.
    """
    if not PETFINDER_KEY or not PETFINDER_SECRET:
        raise RuntimeError("Missing PETFINDER_KEY or PETFINDER_SECRET environment variables.")

    url = "https://api.petfinder.com/v2/oauth2/token"
    form = {
        "grant_type": "client_credentials",
        "client_id": PETFINDER_KEY,
        "client_secret": PETFINDER_SECRET,
    }

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(url, data=form, timeout=HTTP_TIMEOUT)
            if resp.ok:
                token = resp.json()["access_token"]
                return token
            else:
                print(f"❌ Token error (attempt {attempt}): {resp.status_code} {resp.text}")
        except requests.RequestException as e:
            print(f"❌ Token request failed (attempt {attempt}): {e}")

        if attempt < max_retries:
            sleep_s = backoff_base ** attempt + random.uniform(0, 0.5)
            time.sleep(sleep_s)

    raise RuntimeError("Unable to obtain Petfinder token after retries.")

def get_random_cats(access_token: str, limit: int = BATCH_LIMIT) -> List[Dict]:
    """
    Fetch a random batch of cats near the configured location/distance.
    """
    url = "https://api.petfinder.com/v2/animals"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "type": "Cat",
        "limit": limit,
        "sort": "random",
        "location": PET_LOCATION,
        "distance": PET_DISTANCE_MILES,
        "status": "adoptable",
    }
    resp = requests.get(url, headers=headers, params=params, timeout=HTTP_TIMEOUT)
    if not resp.ok:
        print(f"❌ Pet fetch error: {resp.status_code} {resp.text}")
        resp.raise_for_status()
    return resp.json().get("animals", []) or []

# ========== Content helpers ==========
def generate_alt_text(pet: Dict) -> str:
    """
    Create simple, readable alt text for the first image of the pet.
    """
    name = pet.get("name", "Unnamed friend")
    pet_type = pet.get("type", "Pet")
    breeds = pet.get("breeds", {}) or {}
    breed = breeds.get("primary") or breeds.get("secondary") or "mixed breed"
    age = (pet.get("age") or "").lower()
    gender = (pet.get("gender") or "").lower()

    parts = [name, pet_type.lower(), breed.lower()]
    if age:
        parts.append(age)
    if gender:
        parts.append(gender)
    return "Photo of " + " ".join(parts)

def build_status_text(pet: Dict) -> str:
    """
    Compose the Mastodon status text, including a random cat-themed icon.
    """
    icon = get_random_cat_icon()
    name = pet.get("name", "Unnamed friend")
    raw_url = pet.get("url", "") or ""
    clean_url = raw_url.split("?")[0] if raw_url else ""
    return f"{icon} Meet {name}! Available for adoption in/near Boston.\n{clean_url}"

def choose_pet_to_post(access_token: str, recent_ids: set) -> Tuple[Optional[Dict], int]:
    """
    Attempt multiple random batches to find a cat that hasn't been posted recently.
    Preference: pick a pet with at least one photo; otherwise allow text-only.
    Returns (pet, total_candidates_seen)
    """
    total_seen = 0
    for attempt in range(1, MAX_RANDOM_BATCH_ATTEMPTS + 1):
        animals = get_random_cats(access_token, limit=BATCH_LIMIT)
        total_seen += len(animals)

        # Filter out recently posted
        new_candidates = [a for a in animals if a.get("id") not in recent_ids]

        if not new_candidates:
            print(f"ℹ️ Attempt {attempt}/{MAX_RANDOM_BATCH_ATTEMPTS}: all {len(animals)} were posted recently. Trying another random batch...")
            continue

        # Prefer candidates that have photos
        with_photos = [a for a in new_candidates if a.get("photos")]
        chosen = random.choice(with_photos or new_candidates)
        return chosen, total_seen

    return None, total_seen

# ========== Mastodon helpers
