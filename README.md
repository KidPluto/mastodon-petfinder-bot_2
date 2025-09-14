# Mastodon Petfinder Bot 🐾

This bot posts a random adoptable cat from Petfinder to Mastodon every two hours. It searches shelters within a 10 mile radius of Boston (02119).

## Features
- Fetches adoptable cats from the Petfinder API.
- Avoids reposting the same cat within the last 7 days (tracked in a local JSON file).
- Ensures posts include a clean link back to the Petfinder listing.
- Uploads the pet’s photo when available and adds descriptive alt text for accessibility.
- Uses a random cat-related icon in each post (e.g., 🐱, 🐈, 😺, 🐾, 🧶) for variety.
- Configurable via environment variables.
- Runs automatically via GitHub Actions on a schedule (every 2 hours) and supports manual dispatch.

## Example Post
> Meet Bella! 😺 Available for adoption in/near Boston.  
> https://www.petfinder.com/...

## Setup
1. Fork this repository.
2. Create a new application on your Mastodon instance and obtain an access token.
3. Obtain Petfinder API credentials from https://www.petfinder.com/developers/.
4. Add the following secrets in your GitHub repository under Settings → Secrets and variables → Actions:
    - MASTODON_BASE_URL (e.g., https://mastodon.social)
    - MASTODON_ACCESS_TOKEN
    - PETFINDER_KEY
    - PETFINDER_SECRET

Optional (if you plan to use them in your workflow or future enhancements):
- POST_VISIBILITY (e.g., public, unlisted, private)
- HASHTAGS (e.g., #AdoptDontShop #BostonCats)

## Workflows
- bot.yml → Runs the bot every 2 hours and can be run manually.
- Additional test/report workflows are available for diagnostics and experiments.

## Local Testing
You can also run the bot locally:

bash pip install -r requirements.txt export MASTODON_BASE_URL="[https://your.instance](https://your.instance)" export MASTODON_ACCESS_TOKEN="xxxx" export PETFINDER_KEY="xxxx" export PETFINDER_SECRET="xxxx" python mastodon_petfinder_bot.py


## How It Works
- Retrieves an access token from Petfinder and fetches a batch of random cats nearby.
- Skips any cat posted in the last 7 days (based on a local JSON history file).
- Selects a new cat, uploads its photo (if available) with generated alt text, and posts the status to Mastodon with a random cat-themed icon.
- Updates the posted history and prunes entries older than 7 days.

## Troubleshooting
- If nothing posts:
    - Verify all required secrets are present and correct.
    - Check the Actions run logs for HTTP errors from Petfinder or Mastodon.
    - Ensure your Mastodon access token has permission to post.
- If images don’t appear:
    - Make sure the selected pet has a photo on Petfinder.
    - Confirm the instance allows media uploads via API.

## Security Notes
- Never commit your tokens or secrets.
- Use GitHub Actions secrets for all sensitive values.
- Rotate tokens periodically.

## License
MIT
