#!/usr/bin/env python3
import os
import sys
import traceback

REQUIRED_ENV_VARS = [
    "PETFINDER_KEY",
    "PETFINDER_SECRET",
    "MASTODON_BASE_URL",
    "MASTODON_ACCESS_TOKEN",
]

def ensure_env():
    missing = [k for k in REQUIRED_ENV_VARS if not os.getenv(k)]
    if missing:
        print("Missing required environment variables:")
        for k in missing:
            print(f"  - {k}")
        print("\nSet them (example bash):")
        print("  export PETFINDER_KEY=xxxx")
        print("  export PETFINDER_SECRET=xxxx")
        print("  export MASTODON_BASE_URL=https://your.instance")
        print("  export MASTODON_ACCESS_TOKEN=xxxx")
        sys.exit(1)

def main():
    ensure_env()
    try:
        # Import and run the report
        import shelter_cats_report
        shelter_cats_report.main()
        print("Report posted successfully.")
    except SystemExit:
        raise
    except Exception as e:
        print("Error while running shelter_cats_report:")
        print(e)
        traceback.print_exc()
        sys.exit(2)

if __name__ == "__main__":
    main()