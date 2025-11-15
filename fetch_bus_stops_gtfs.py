#!/usr/bin/env python3
"""
Fetch all bus stops in Västra Götalands län using Trafiklab GTFS Sweden 3
This is an alternative method that downloads a complete GTFS dataset instead of querying an API.

To use this script:
1. Register at https://www.trafiklab.se/
2. Create a project and subscribe to "GTFS Sweden 3" API
3. Copy your API key and set it in the API_KEY variable below
"""

import requests
import zipfile
import csv
import json
import io
from typing import List, Dict, Set
from pathlib import Path

# Configuration
API_KEY = "YOUR_TRAFIKLAB_API_KEY_HERE"  # Get from https://www.trafiklab.se/
GTFS_URL = f"https://opendata.samtrafiken.se/gtfs-sweden/sweden.zip?key={API_KEY}"
OUTPUT_FILE = "bus_stops_gtfs.json"
CACHE_DIR = Path("gtfs_cache")

# Counties in Västra Götaland (for filtering)
VASTRA_GOTALAND_MUNICIPALITIES = {
    'Göteborg', 'Mölndal', 'Partille', 'Härryda', 'Öckerö', 'Ale', 'Lerum',
    'Vårgårda', 'Bollebygd', 'Grästorp', 'Essunga', 'Karlsborg', 'Gullspång',
    'Tranemo', 'Bengtsfors', 'Mellerud', 'Lilla Edet', 'Mark', 'Svenljunga',
    'Herrljunga', 'Vara', 'Götene', 'Tibro', 'Töreboda', 'Göteborg',
    'Kungälv', 'Stenungsund', 'Tjörn', 'Orust', 'Sotenäs', 'Munkedal',
    'Tanum', 'Dals-Ed', 'Färgelanda', 'Åmål', 'Säffle', 'Kil', 'Eda',
    'Torsby', 'Storfors', 'Hammarö', 'Kristinehamn', 'Filipstad', 'Hagfors',
    'Arvika', 'Sunne', 'Karlstad', 'Grums', 'Årjäng', 'Lysekil', 'Uddevalla',
    'Strömstad', 'Vänersborg', 'Trollhättan', 'Alingsås', 'Borås', 'Ulricehamn',
    'Åmål', 'Mariestad', 'Lidköping', 'Skara', 'Skövde', 'Hjo', 'Tidaholm',
    'Falköping'
}


def download_gtfs_data() -> bytes:
    """Download GTFS Sweden 3 ZIP file"""
    print("=" * 70)
    print("Downloading GTFS Sweden 3 dataset from Trafiklab...")
    print("=" * 70)
    print(f"URL: {GTFS_URL.replace(API_KEY, 'XXXX')}")
    print("\nThis may take a few minutes (file is ~100-200 MB)...")

    try:
        response = requests.get(GTFS_URL, stream=True, timeout=300)
        response.raise_for_status()

        # Download with progress indication
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        chunks = []

        for chunk in response.iter_content(chunk_size=1024*1024):  # 1MB chunks
            if chunk:
                chunks.append(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\rDownloading: {percent:.1f}% ({downloaded // (1024*1024)}MB / {total_size // (1024*1024)}MB)", end='')

        print("\n✓ Download complete!")
        return b''.join(chunks)

    except requests.exceptions.RequestException as e:
        print(f"\n✗ Download failed: {e}")
        if "404" in str(e):
            print("\nPossible issues:")
            print("  1. Invalid API key - check your Trafiklab API key")
            print("  2. Not subscribed to GTFS Sweden 3 API")
            print("  3. API key doesn't have access to this dataset")
        return None


def extract_stops_from_gtfs(zip_data: bytes) -> List[Dict]:
    """Extract stops from GTFS stops.txt file"""
    print("\n" + "=" * 70)
    print("Extracting stops from GTFS data...")
    print("=" * 70)

    stops = []

    try:
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            # List available files
            print("\nFiles in GTFS archive:")
            for name in sorted(zf.namelist()):
                print(f"  - {name}")

            # Read stops.txt
            if 'stops.txt' not in zf.namelist():
                print("\n✗ Error: stops.txt not found in GTFS archive")
                return []

            print("\n✓ Reading stops.txt...")
            with zf.open('stops.txt') as f:
                # Decode from bytes to text
                text_data = io.TextIOWrapper(f, encoding='utf-8')
                reader = csv.DictReader(text_data)

                all_stops = list(reader)
                print(f"✓ Found {len(all_stops)} total stops in Sweden")

                # Also read agency.txt to filter by Västtrafik
                vasttrafik_agency_ids = set()
                if 'agency.txt' in zf.namelist():
                    with zf.open('agency.txt') as af:
                        agency_text = io.TextIOWrapper(af, encoding='utf-8')
                        agency_reader = csv.DictReader(agency_text)
                        for agency in agency_reader:
                            if 'Västtrafik' in agency.get('agency_name', '') or \
                               'Vasttrafik' in agency.get('agency_name', ''):
                                vasttrafik_agency_ids.add(agency.get('agency_id'))
                                print(f"  Found Västtrafik agency: {agency.get('agency_name')} (ID: {agency.get('agency_id')})")

                # Try to filter stops by zone_id or stop_name containing Västra Götaland keywords
                print("\n✓ Filtering stops for Västra Götalands län...")
                for stop in all_stops:
                    stop_name = stop.get('stop_name', '')
                    stop_id = stop.get('stop_id', '')

                    # Check if stop belongs to Västra Götaland region
                    # GTFS often includes zone info or stop IDs with region codes
                    is_vasttrafik = any(keyword in stop_id.upper() for keyword in ['VT', 'VASTTRAFIK', 'GBGR'])

                    # Check stop name for municipalities
                    is_in_region = any(mun in stop_name for mun in VASTRA_GOTALAND_MUNICIPALITIES)

                    if is_vasttrafik or is_in_region:
                        stops.append({
                            'stop_id': stop.get('stop_id'),
                            'stop_name': stop.get('stop_name'),
                            'latitude': float(stop.get('stop_lat', 0)),
                            'longitude': float(stop.get('stop_lon', 0)),
                            'zone_id': stop.get('zone_id', ''),
                            'stop_code': stop.get('stop_code', ''),
                            'location_type': stop.get('location_type', '0'),
                            'parent_station': stop.get('parent_station', ''),
                            'platform_code': stop.get('platform_code', ''),
                            'source': 'GTFS Sweden 3'
                        })

                print(f"✓ Filtered to {len(stops)} stops in Västra Götalands län")

                # If filtering didn't work well, offer all stops
                if len(stops) < 100:
                    print("\n⚠ Warning: Filter may be too restrictive, returning ALL Sweden stops")
                    print("  You can manually filter the JSON file afterwards")
                    stops = [{
                        'stop_id': s.get('stop_id'),
                        'stop_name': s.get('stop_name'),
                        'latitude': float(s.get('stop_lat', 0)),
                        'longitude': float(s.get('stop_lon', 0)),
                        'zone_id': s.get('zone_id', ''),
                        'stop_code': s.get('stop_code', ''),
                        'location_type': s.get('location_type', '0'),
                        'parent_station': s.get('parent_station', ''),
                        'platform_code': s.get('platform_code', ''),
                        'source': 'GTFS Sweden 3'
                    } for s in all_stops]

    except Exception as e:
        print(f"✗ Error extracting stops: {e}")
        import traceback
        traceback.print_exc()
        return []

    return stops


def main():
    """Main function"""
    print("\n" + "=" * 70)
    print("GTFS Sweden 3 Bus Stop Fetcher")
    print("Alternative method using Trafiklab's complete GTFS dataset")
    print("=" * 70)

    # Check API key
    if API_KEY == "YOUR_TRAFIKLAB_API_KEY_HERE":
        print("\n✗ Error: Please set your Trafiklab API key!")
        print("\nSteps to get started:")
        print("  1. Go to https://www.trafiklab.se/")
        print("  2. Create a free account")
        print("  3. Create a project")
        print("  4. Subscribe to 'GTFS Sweden 3' API (Bronze tier is free)")
        print("  5. Copy your API key and set it in this script")
        print("\n  API_KEY = 'your-key-here'")
        return

    # Download GTFS data
    zip_data = download_gtfs_data()
    if not zip_data:
        return

    # Extract stops
    stops = extract_stops_from_gtfs(zip_data)
    if not stops:
        print("\n✗ No stops were extracted")
        return

    # Save to JSON
    print(f"\n{'=' * 70}")
    print(f"Saving {len(stops)} stops to {OUTPUT_FILE}...")
    print(f"{'=' * 70}")

    output_data = {
        'total_stops': len(stops),
        'source': 'Trafiklab GTFS Sweden 3',
        'region': 'Västra Götalands län',
        'stops': stops
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"✓ Saved to {OUTPUT_FILE}\n")

    # Show samples
    if stops:
        print("Sample stops:")
        for stop in stops[:10]:
            print(f"  • {stop['stop_name']} ({stop['latitude']}, {stop['longitude']})")

        # Statistics
        print(f"\nTotal stops: {len(stops)}")

        # Count location types
        location_types = {}
        for stop in stops:
            loc_type = stop.get('location_type', '0')
            location_types[loc_type] = location_types.get(loc_type, 0) + 1

        print("\nLocation types:")
        type_names = {'0': 'Stop/Platform', '1': 'Station', '2': 'Entrance/Exit', '3': 'Generic Node'}
        for loc_type, count in sorted(location_types.items()):
            type_name = type_names.get(loc_type, f'Type {loc_type}')
            print(f"  - {type_name}: {count}")


if __name__ == "__main__":
    main()
