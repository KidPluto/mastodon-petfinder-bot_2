import os
import random
import requests
from mastodon import Mastodon
from dotenv import load_dotenv

from test_petfinder import fetch_random_pet, get_valid_token

def get_pet_with_photo(max_retries=5):
    for attempt in range(max_retries):
        pet = fetch_random_pet()
        if pet.get("primary_photo_cropped"):
            return pet
        print(f"Retry {attempt+1}/{max_retries}: {pet['name']} had no photo")
    print("No pet with photo found after retries, using last one anyway")
    return pet

def main():
    load_dotenv()
    pet = get_pet_with_photo()
    print("---- Posting Pet ----")
    print(f"Name: {pet['name']}")
    print(f"Type: {pet['type']}, Age: {pet['age']}, Breed: {pet['breeds']['primary']}")
    print(f"URL: {pet['url']}")
    if pet.get("primary_photo_cropped"):
        print(f"Photo: {pet['primary_photo_cropped']['large']}")

    mastodon = Mastodon(
        access_token=os.getenv("MASTODON_ACCESS_TOKEN"),
        api_base_url=os.getenv("MASTODON_BASE_URL"),
    )
    status = f"Meet {pet['name']}! {pet['type']} ({pet['age']}, {pet['breeds']['primary']}) — {pet['url']}"
    if os.getenv("HASHTAGS"):
        status += "\n" + os.getenv("HASHTAGS")

    media_id = None
    if pet.get("primary_photo_cropped"):
        img_url = pet["primary_photo_cropped"]["large"]
        try:
            resp = requests.get(img_url, timeout=15)
            resp.raise_for_status()
            with open("pet.jpg", "wb") as f:
                f.write(resp.content)
            media_id = mastodon.media_post("pet.jpg")
            print("Photo uploaded successfully")
        except Exception as e:
            print(f"Warning: could not upload photo: {e}")

    mastodon.status_post(
        status,
        media_ids=[media_id] if media_id else None,
        visibility=os.getenv("POST_VISIBILITY", "public")
    )
    print("Post successful!")

if __name__ == "__main__":
    main()
