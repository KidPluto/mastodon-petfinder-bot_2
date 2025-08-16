import os
import random
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("PETFINDER_KEY")
API_SECRET = os.getenv("PETFINDER_SECRET")
TOKEN_URL = "https://api.petfinder.com/v2/oauth2/token"
ANIMALS_URL = "https://api.petfinder.com/v2/animals"

def get_valid_token():
    resp = requests.post(TOKEN_URL, data={
        "grant_type": "client_credentials",
        "client_id": API_KEY,
        "client_secret": API_SECRET,
    })
    resp.raise_for_status()
    return resp.json()["access_token"]

def fetch_random_pet():
    token = get_valid_token()
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(ANIMALS_URL, headers=headers, params={
        "type": random.choice(["Dog", "Cat"]),
        "limit": 100,
    })
    resp.raise_for_status()
    animals = resp.json().get("animals", [])
    if not animals:
        raise Exception("No animals found")
    return random.choice(animals)

if __name__ == "__main__":
    pet = fetch_random_pet()
    print("Fetched:", pet["name"], pet.get("primary_photo_cropped"))
