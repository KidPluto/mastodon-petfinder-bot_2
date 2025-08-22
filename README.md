# Mastodon Petfinder Bot 🐾

This bot posts a random adoptable **cat** from [Petfinder](https://www.petfinder.com/) to Mastodon once an hour.  Shelters in a 10 mile radius of Boston will be queried.

## Features
- Fetches adoptable cats from Petfinder API.
- Retries up to 5 times to ensure the pet has a photo before posting.
- Posts pet’s name, type, age, breed, and adoption link.  Also creates alt text for the photo, from other data about the cat.
- Uploads the pet’s photo (if available).
- Hashtags and post visibility configurable via environment variables.
- Runs automatically every hour via GitHub Actions.

## Example Post

Here’s what a typical Mastodon post looks like (example only):

![Example Mastodon Post](docs/example-post.png)

> Meet Bella! Dog (Young, Labrador Retriever) — [adopt me on Petfinder](https://www.petfinder.com/)

## Setup

1. **Fork this repo** into your own GitHub account.
2. Create a new application on your Mastodon instance to get an access token.
3. Get Petfinder API credentials from https://www.petfinder.com/developers/.
4. Add the following secrets in your GitHub repo under **Settings → Secrets → Actions**:

   - `MASTODON_BASE_URL` (e.g. `https://mastodon.social`)
   - `MASTODON_ACCESS_TOKEN`
   - `PETFINDER_KEY`
   - `PETFINDER_SECRET`

## Workflows

- **bot.yml** → Runs hourly, posts to Mastodon.
- **test.yml** → Can be triggered manually from GitHub Actions to test the Petfinder API and print debug info.
- **test_mastodon.yml** 
- **test_petfinder_shelters.yml**

## Local Testing

You can also run the bot locally:

```bash
pip install -r requirements.txt
export MASTODON_BASE_URL=https://your.instance
export MASTODON_ACCESS_TOKEN=xxxx
export PETFINDER_KEY=xxxx
export PETFINDER_SECRET=xxxx
python mastodon_petfinder_bot.py
```

## License
MIT
