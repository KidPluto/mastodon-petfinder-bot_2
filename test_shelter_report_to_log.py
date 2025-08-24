#!/usr/bin/env python3
import logging
import sys

# Not seeing this on the repo, after pushing it, so adding this line and trying again

from shelter_cats_report import get_petfinder_token, get_shelters, get_cat_count

def build_report():
    token = get_petfinder_token()
    shelters = get_shelters(token)

    lines = []
    for shelter in shelters:
        name = shelter.get('name')
        org_id = shelter.get('id')
        cat_count = get_cat_count(token, org_id)
        lines.append(f"{name}: {cat_count} cats available")

    header = "Shelters near 02119 (10mi):"
    return header + "\n" + "\n".join(lines)

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        stream=sys.stdout,
    )
    try:
        report = build_report()
        logging.info("Shelter report generated:\n%s", report)
    except Exception:
        logging.exception("Failed to generate shelter report")
        sys.exit(1)

if __name__ == "__main__":
    main()