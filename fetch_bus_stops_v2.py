#!/usr/bin/env python3
"""
Fetch all bus stop coordinates from Västtrafik API
Supports multiple API versions with configurable endpoints
"""

import requests
import json
import time
from typing import List, Dict
from itertools import product

# Configuration - UPDATE THESE based on your API subscription
CONFIG = {
    # Your API credentials (Base64 encoded client_id:client_secret)
    "api_key": "RXFrWXB0azVuNm43Slg5VmdmbGhkSnl3cnVrYTpNU0NqbEswaFNfa0dJd1RjYmlKSHRaVDNxRXNh",

    # API Version - try different versions if one doesn't work
    "version": "v2",  # Options: "v2", "v4"

    # Endpoints will be set based on version below
    "token_url": None,
    "base_url": None,
    "output_file": "bus_stops.json"
}

# Set endpoints based on version
if CONFIG["version"] == "v2":
    CONFIG["token_url"] = "https://api.vasttrafik.se/token"
    CONFIG["base_url"] = "https://api.vasttrafik.se/bin/rest.exe/v2"
elif CONFIG["version"] == "v4":
    CONFIG["token_url"] = "https://api.vasttrafik.se/token"
    CONFIG["base_url"] = "https://ext-api.vasttrafik.se/pr/v4"


class VasttrafikAPI:
    """Västtrafik API client supporting multiple versions"""

    def __init__(self, config: dict):
        self.config = config
        self.access_token = None
        self.token_expiry = 0

    def authenticate(self):
        """Get OAuth2 access token"""
        print(f"Authenticating with Västtrafik API {self.config['version']}...")
        print(f"Token URL: {self.config['token_url']}")

        headers = {
            "Authorization": f"Basic {self.config['api_key']}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {
            "grant_type": "client_credentials"
        }

        try:
            response = requests.post(
                self.config['token_url'],
                headers=headers,
                data=data,
                timeout=10
            )
            response.raise_for_status()
            token_data = response.json()

            self.access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            self.token_expiry = time.time() + expires_in - 60

            print(f"✓ Authentication successful!")
            print(f"  Token type: {token_data.get('token_type', 'Bearer')}")
            print(f"  Expires in: {expires_in} seconds")
            return True

        except requests.exceptions.RequestException as e:
            print(f"✗ Authentication failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"  Status: {e.response.status_code}")
                print(f"  Response: {e.response.text}")
            print("\nTroubleshooting:")
            print("  1. Verify your API key is correct")
            print("  2. Check you've subscribed to the correct API on developer.vasttrafik.se")
            print("  3. Try changing CONFIG['version'] to 'v2' or 'v4'")
            print("  4. Check if your API subscription is active")
            return False

    def ensure_authenticated(self):
        """Ensure we have a valid access token"""
        if not self.access_token or time.time() >= self.token_expiry:
            return self.authenticate()
        return True

    def search_locations_v2(self, query: str) -> List[Dict]:
        """Search locations using v2 API"""
        if not self.ensure_authenticated():
            return []

        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        params = {
            "input": query,
            "format": "json"
        }

        try:
            url = f"{self.config['base_url']}/location.name"
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # v2 API has different response structure
            locations = data.get("LocationList", {}).get("StopLocation", [])
            if isinstance(locations, dict):
                locations = [locations]

            print(f"  Found {len(locations)} stops for '{query}'")
            return locations

        except requests.exceptions.RequestException as e:
            print(f"  ✗ Error: {e}")
            return []

    def search_all_stops_v2(self) -> List[Dict]:
        """Get all stops using v2 API location.allstops endpoint"""
        if not self.ensure_authenticated():
            return []

        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        params = {
            "format": "json"
        }

        try:
            url = f"{self.config['base_url']}/location.allstops"
            print(f"\nFetching all stops from {url}")
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            # v2 API returns StopLocation array
            locations = data.get("LocationList", {}).get("StopLocation", [])
            if isinstance(locations, dict):
                locations = [locations]

            print(f"✓ Found {len(locations)} total stops")
            return locations

        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching all stops: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"  Response: {e.response.text[:500]}")
            return []

    def search_locations_v4(self, query: str, limit: int = 1000) -> List[Dict]:
        """Search locations using v4 API"""
        if not self.ensure_authenticated():
            return []

        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        params = {
            "q": query,
            "limit": limit,
            "types": "stoparea"
        }

        try:
            url = f"{self.config['base_url']}/locations/by-text"
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            print(f"  Found {len(results)} stops for '{query}'")
            return results

        except requests.exceptions.RequestException as e:
            print(f"  ✗ Error: {e}")
            return []


def extract_stop_info_v2(stops: List[Dict]) -> List[Dict]:
    """Extract info from v2 API stops"""
    extracted = []
    for stop in stops:
        info = {
            "id": stop.get("id"),
            "name": stop.get("name"),
            "latitude": float(stop.get("lat", 0)),
            "longitude": float(stop.get("lon", 0)),
            "track": stop.get("track", ""),
            "api_version": "v2"
        }
        extracted.append(info)
    return extracted


def extract_stop_info_v4(stops: List[Dict]) -> List[Dict]:
    """Extract info from v4 API stops"""
    extracted = []
    for stop in stops:
        info = {
            "gid": stop.get("gid"),
            "name": stop.get("name"),
            "latitude": stop.get("latitude"),
            "longitude": stop.get("longitude"),
            "type": stop.get("locationType"),
            "municipality": stop.get("municipality", ""),
            "api_version": "v4"
        }
        extracted.append(info)
    return extracted


def fetch_stops_v2(api: VasttrafikAPI) -> List[Dict]:
    """Fetch all stops using v2 API"""
    print("\n=== Using v2 API: location.allstops ===")

    # Try the allstops endpoint first
    stops = api.search_all_stops_v2()

    if not stops:
        print("\n=== Fallback: Text search strategy ===")
        all_stops = {}
        seen_ids = set()

        # Fallback to text search
        search_terms = list("abcdefghijklmnopqrstuvwxyzåäö")

        for term in search_terms:
            print(f"\nSearching for '{term}'...")
            results = api.search_locations_v2(term)

            for stop in results:
                stop_id = stop.get("id")
                if stop_id and stop_id not in seen_ids:
                    seen_ids.add(stop_id)
                    all_stops[stop_id] = stop

            print(f"Total unique stops: {len(all_stops)}")
            time.sleep(0.3)

        stops = list(all_stops.values())

    return extract_stop_info_v2(stops)


def fetch_stops_v4(api: VasttrafikAPI) -> List[Dict]:
    """Fetch all stops using v4 API"""
    print("\n=== Using v4 API: Text search ===")
    all_stops = {}
    seen_gids = set()

    search_terms = list("abcdefghijklmnopqrstuvwxyzåäö") + [
        "gatan", "vägen", "station", "centrum"
    ]

    for term in search_terms:
        print(f"\nSearching for '{term}'...")
        results = api.search_locations_v4(term)

        for stop in results:
            gid = stop.get("gid")
            if gid and gid not in seen_gids:
                seen_gids.add(gid)
                all_stops[gid] = stop

        print(f"Total unique stops: {len(all_stops)}")
        time.sleep(0.3)

    return extract_stop_info_v4(list(all_stops.values()))


def main():
    """Main function"""
    print("=" * 70)
    print("Västtrafik Bus Stop Coordinate Fetcher")
    print("=" * 70)
    print(f"API Version: {CONFIG['version']}")
    print(f"Base URL: {CONFIG['base_url']}")
    print("=" * 70)

    api = VasttrafikAPI(CONFIG)

    # Fetch stops based on version
    if CONFIG["version"] == "v2":
        stops = fetch_stops_v2(api)
    elif CONFIG["version"] == "v4":
        stops = fetch_stops_v4(api)
    else:
        print(f"✗ Unsupported API version: {CONFIG['version']}")
        return

    print(f"\n{'=' * 70}")
    print(f"Total stops found: {len(stops)}")
    print(f"{'=' * 70}\n")

    if not stops:
        print("⚠ No stops were found. Please check:")
        print("  1. Your API credentials are correct")
        print("  2. You have an active API subscription")
        print("  3. The API version is correct")
        return

    # Save to JSON
    output_data = {
        "total_stops": len(stops),
        "api_version": CONFIG["version"],
        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "stops": stops
    }

    with open(CONFIG["output_file"], 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"✓ Saved {len(stops)} stops to {CONFIG['output_file']}\n")

    # Print samples and statistics
    if stops:
        print("Sample stops:")
        for stop in stops[:5]:
            name = stop.get('name', 'Unknown')
            lat = stop.get('latitude', 0)
            lon = stop.get('longitude', 0)
            print(f"  • {name} ({lat}, {lon})")


if __name__ == "__main__":
    main()
