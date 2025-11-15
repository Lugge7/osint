#!/usr/bin/env python3
"""
Fetch all bus stop coordinates from Västtrafik API v4
"""

import requests
import json
import base64
import time
from typing import List, Dict, Set
from itertools import product

# Configuration
API_KEY = "RXFrWXB0azVuNm43Slg5VmdmbGhkSnl3cnVrYTpNU0NqbEswaFNfa0dJd1RjYmlKSHRaVDNxRXNh"
BASE_URL = "https://ext-api.vasttrafik.se/pr/v4"
TOKEN_URL = "https://api.vasttrafik.se/token"
OUTPUT_FILE = "bus_stops.json"


class VasttrafikAPI:
    """Västtrafik API client"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.access_token = None
        self.token_expiry = 0

    def authenticate(self):
        """Get OAuth2 access token"""
        print("Authenticating with Västtrafik API...")

        headers = {
            "Authorization": f"Basic {self.api_key}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {
            "grant_type": "client_credentials",
            "scope": "device_1"  # Device ID scope
        }

        try:
            response = requests.post(TOKEN_URL, headers=headers, data=data)
            response.raise_for_status()
            token_data = response.json()

            self.access_token = token_data["access_token"]
            # Set expiry time (subtract 60 seconds for safety margin)
            self.token_expiry = time.time() + token_data.get("expires_in", 3600) - 60

            print(f"✓ Authentication successful. Token expires in {token_data.get('expires_in', 'unknown')} seconds")
            return True

        except requests.exceptions.RequestException as e:
            print(f"✗ Authentication failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"  Response: {e.response.text}")
            return False

    def ensure_authenticated(self):
        """Ensure we have a valid access token"""
        if not self.access_token or time.time() >= self.token_expiry:
            return self.authenticate()
        return True

    def search_locations_by_text(self, query: str, limit: int = 1000) -> List[Dict]:
        """Search for locations by text"""
        if not self.ensure_authenticated():
            return []

        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        params = {
            "q": query,
            "limit": limit,
            "types": "stoparea"  # Only get stop areas
        }

        try:
            url = f"{BASE_URL}/locations/by-text"
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            print(f"  Found {len(results)} stops for query '{query}'")
            return results

        except requests.exceptions.RequestException as e:
            print(f"  ✗ Error searching for '{query}': {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"    Response: {e.response.text}")
            return []

    def search_locations_by_coordinates(self, lat: float, lon: float, radius: int = 5000, limit: int = 1000) -> List[Dict]:
        """Search for locations near coordinates"""
        if not self.ensure_authenticated():
            return []

        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        params = {
            "latitude": lat,
            "longitude": lon,
            "radiusInMeters": radius,
            "limit": limit,
            "types": "stoparea"
        }

        try:
            url = f"{BASE_URL}/locations/by-coordinates"
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            return results

        except requests.exceptions.RequestException as e:
            print(f"  ✗ Error searching coordinates ({lat}, {lon}): {e}")
            return []


def fetch_all_stops() -> List[Dict]:
    """Fetch all bus stops using multiple strategies"""
    api = VasttrafikAPI(API_KEY)
    all_stops = {}
    seen_gids = set()

    # Strategy 1: Search by common Swedish letters and terms
    print("\n=== Strategy 1: Text Search ===")
    search_terms = [
        # Single letters (Swedish alphabet)
        'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
        'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
        'å', 'ä', 'ö',
        # Common Swedish location terms
        'gatan', 'vägen', 'plan', 'torg', 'station', 'hållplats',
        'centrum', 'kyrka', 'skola', 'park',
        # Numbers
        '1', '2', '3', '4', '5', '6', '7', '8', '9', '0'
    ]

    for term in search_terms:
        print(f"\nSearching for '{term}'...")
        results = api.search_locations_by_text(term)

        for stop in results:
            gid = stop.get("gid")
            if gid and gid not in seen_gids:
                seen_gids.add(gid)
                all_stops[gid] = stop

        print(f"Total unique stops so far: {len(all_stops)}")
        time.sleep(0.2)  # Rate limiting

    # Strategy 2: Grid search by coordinates (Gothenburg region)
    # Västtrafik covers Gothenburg and surrounding areas
    # Approximate bounds: lat 57.4-58.0, lon 11.5-12.5
    print("\n=== Strategy 2: Grid Search by Coordinates ===")

    lat_min, lat_max = 57.4, 58.0
    lon_min, lon_max = 11.5, 12.5
    grid_step = 0.1  # Approximately 10km

    lat_points = [lat_min + i * grid_step for i in range(int((lat_max - lat_min) / grid_step) + 1)]
    lon_points = [lon_min + i * grid_step for i in range(int((lon_max - lon_min) / grid_step) + 1)]

    total_points = len(lat_points) * len(lon_points)
    current_point = 0

    for lat, lon in product(lat_points, lon_points):
        current_point += 1
        print(f"\nSearching grid point {current_point}/{total_points} ({lat:.2f}, {lon:.2f})...")

        results = api.search_locations_by_coordinates(lat, lon, radius=10000)

        new_stops = 0
        for stop in results:
            gid = stop.get("gid")
            if gid and gid not in seen_gids:
                seen_gids.add(gid)
                all_stops[gid] = stop
                new_stops += 1

        if new_stops > 0:
            print(f"  Added {new_stops} new stops")
        print(f"Total unique stops so far: {len(all_stops)}")

        time.sleep(0.2)  # Rate limiting

    return list(all_stops.values())


def extract_stop_info(stops: List[Dict]) -> List[Dict]:
    """Extract relevant information from stops"""
    extracted = []

    for stop in stops:
        info = {
            "gid": stop.get("gid"),
            "name": stop.get("name"),
            "latitude": stop.get("latitude"),
            "longitude": stop.get("longitude"),
            "type": stop.get("locationType"),
        }

        # Add municipality if available
        if "municipality" in stop:
            info["municipality"] = stop["municipality"]

        # Add track info if available
        if "track" in stop:
            info["track"] = stop["track"]

        extracted.append(info)

    return extracted


def main():
    """Main function"""
    print("=" * 60)
    print("Västtrafik Bus Stop Coordinate Fetcher")
    print("=" * 60)

    # Fetch all stops
    stops = fetch_all_stops()

    print(f"\n{'=' * 60}")
    print(f"Total stops found: {len(stops)}")
    print(f"{'=' * 60}\n")

    # Extract relevant information
    extracted_stops = extract_stop_info(stops)

    # Save to JSON file
    output_data = {
        "total_stops": len(extracted_stops),
        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "stops": extracted_stops
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"✓ Saved {len(extracted_stops)} stops to {OUTPUT_FILE}")

    # Print some statistics
    if extracted_stops:
        print("\nSample stops:")
        for stop in extracted_stops[:5]:
            print(f"  - {stop['name']} ({stop['latitude']}, {stop['longitude']})")

        # Count by type
        types = {}
        for stop in extracted_stops:
            stop_type = stop.get('type', 'unknown')
            types[stop_type] = types.get(stop_type, 0) + 1

        print("\nStop types:")
        for stop_type, count in types.items():
            print(f"  - {stop_type}: {count}")


if __name__ == "__main__":
    main()
