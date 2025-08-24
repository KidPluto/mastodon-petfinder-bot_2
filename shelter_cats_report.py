# shelter_cats_report.py
import os
import requests
from mastodon import Mastodon

PETFINDER_KEY = os.environ['PETFINDER_KEY']
PETFINDER_SECRET = os.environ['PETFINDER_SECRET']
MASTODON_BASE_URL = os.environ['MASTODON_BASE_URL']
MASTODON_ACCESS_TOKEN = os.environ['MASTODON_ACCESS_TOKEN']

def get_petfinder_token():
    resp = requests.post(
        'https://api.petfinder.com/v2/oauth2/token',
        data={'grant_type': 'client_credentials', 'client_id': PETFINDER_KEY, 'client_secret': PETFINDER_SECRET}
    )
    return resp.json()['access_token']

def get_shelters(token):
    url = 'https://api.petfinder.com/v2/organizations'
    params = {'location': '02119', 'distance': 10, 'limit': 50}
    headers = {'Authorization': f'Bearer {token}'}
    resp = requests.get(url, headers=headers, params=params)
    return resp.json().get('organizations', [])

def get_cat_count(token, org_id):
    url = 'https://api.petfinder.com/v2/animals'
    params = {'organization': org_id, 'type': 'Cat', 'status': 'adoptable', 'limit': 1}
    headers = {'Authorization': f'Bearer {token}'}
    resp = requests.get(url, headers=headers, params=params)
    return resp.json().get('pagination', {}).get('total_count', 0)

def main():
    token = get_petfinder_token()
    shelters = get_shelters(token)
    report_lines = []
    for shelter in shelters:
        name = shelter.get('name')
        org_id = shelter.get('id')
        cat_count = get_cat_count(token, org_id)
        report_lines.append(f"{name}: {cat_count} cats available")
    report = "Shelters near 02119 (10mi):\n" + "\n".join(report_lines)
    mastodon = Mastodon(
        api_base_url=MASTODON_BASE_URL,
        access_token=MASTODON_ACCESS_TOKEN
    )
    mastodon.toot(report)

if __name__ == "__main__":
    main()