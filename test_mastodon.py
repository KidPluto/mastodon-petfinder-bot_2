import os
from mastodon import Mastodon

mastodon = Mastodon(
    access_token=os.getenv("MASTODON_ACCESS_TOKEN"),
    api_base_url=os.getenv("MASTODON_BASE_URL")
)

# Try to post a simple status
mastodon.status_post("Hello from my test Mastodon bot! 🚀")
print("✅ Successfully posted to Mastodon")
