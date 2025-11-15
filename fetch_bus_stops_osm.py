#!/usr/bin/env python3
"""
Fetch all bus stops in Västra Götalands län using OpenStreetMap Overpass API
This method doesn't require any API keys and uses community-sourced geographic data.

Advantages:
- No API key required
- Free and open data
- Global coverage
- Community maintained

Note: OSM data quality varies by region. May not be as complete as official sources.
"""

import requests
import json
import time
from typing import List, Dict

# Configuration
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OUTPUT_FILE = "bus_stops_osm.json"

# Västra Götalands län approximate bounding box
# Format: (min_lat, min_lon, max_lat, max_lon)
BOUNDING_BOX = (57.3, 11.3, 59.0, 14.5)  # Covers Västra Götaland region


def build_overpass_query(bbox: tuple) -> str:
    """Build Overpass QL query for bus stops in bounding box"""
    min_lat, min_lon, max_lat, max_lon = bbox

    # Overpass QL query
    # Searches for nodes and ways tagged as public_transport=stop_position or platform, or highway=bus_stop
    query = f"""
    [out:json][timeout:180];
    (
      // Bus stops (legacy tagging)
      node["highway"="bus_stop"]({min_lat},{min_lon},{max_lat},{max_lon});

      // Public transport stops (new tagging scheme)
      node["public_transport"="stop_position"]({min_lat},{min_lon},{max_lat},{max_lon});
      node["public_transport"="platform"]["bus"="yes"]({min_lat},{min_lon},{max_lat},{max_lon});
      node["public_transport"="station"]({min_lat},{min_lon},{max_lat},{max_lon});

      // Platform ways (areas)
      way["public_transport"="platform"]["bus"="yes"]({min_lat},{min_lon},{max_lat},{max_lon});
    );
    out center;
    """

    return query


def query_overpass(query: str) -> Dict:
    """Execute Overpass API query"""
    print("Querying OpenStreetMap Overpass API...")
    print(f"Query bounding box: {BOUNDING_BOX}")
    print("\nThis may take 30-60 seconds...\n")

    try:
        response = requests.post(
            OVERPASS_URL,
            data={'data': query},
            timeout=200
        )
        response.raise_for_status()

        print("✓ Query successful!")
        return response.json()

    except requests.exceptions.Timeout:
        print("✗ Query timed out. The area might be too large.")
        print("  Try reducing the bounding box or use a different Overpass instance.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"✗ Query failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  Response: {e.response.text[:500]}")
        return None


def extract_stops_from_osm(data: Dict) -> List[Dict]:
    """Extract stop information from OSM data"""
    if not data or 'elements' not in data:
        return []

    stops = []
    seen_coords = set()  # Deduplicate by coordinates

    for element in data['elements']:
        # Get coordinates
        if element['type'] == 'node':
            lat = element.get('lat')
            lon = element.get('lon')
        elif element['type'] == 'way' and 'center' in element:
            # For way elements, use the center point
            lat = element['center'].get('lat')
            lon = element['center'].get('lon')
        else:
            continue

        if not lat or not lon:
            continue

        # Deduplicate by coordinates (rounded to 5 decimals)
        coord_key = (round(lat, 5), round(lon, 5))
        if coord_key in seen_coords:
            continue
        seen_coords.add(coord_key)

        # Extract tags
        tags = element.get('tags', {})

        # Get stop name (try multiple fields)
        name = (tags.get('name') or
                tags.get('ref') or
                tags.get('alt_name') or
                'Unnamed stop')

        # Determine stop type
        if tags.get('highway') == 'bus_stop':
            stop_type = 'bus_stop'
        elif tags.get('public_transport') == 'stop_position':
            stop_type = 'stop_position'
        elif tags.get('public_transport') == 'platform':
            stop_type = 'platform'
        elif tags.get('public_transport') == 'station':
            stop_type = 'station'
        else:
            stop_type = 'unknown'

        stop = {
            'osm_id': element.get('id'),
            'osm_type': element.get('type'),
            'name': name,
            'latitude': lat,
            'longitude': lon,
            'stop_type': stop_type,
            'operator': tags.get('operator', ''),
            'network': tags.get('network', ''),
            'ref': tags.get('ref', ''),
            'shelter': tags.get('shelter', ''),
            'bench': tags.get('bench', ''),
            'source': 'OpenStreetMap'
        }

        # Add additional useful tags
        if 'wheelchair' in tags:
            stop['wheelchair'] = tags['wheelchair']
        if 'tactile_paving' in tags:
            stop['tactile_paving'] = tags['tactile_paving']

        stops.append(stop)

    return stops


def filter_by_operator(stops: List[Dict]) -> List[Dict]:
    """Filter stops to only include Västtrafik operated ones"""
    vasttrafik_stops = []
    other_stops = []

    for stop in stops:
        operator = stop.get('operator', '').lower()
        network = stop.get('network', '').lower()

        if 'västtrafik' in operator or 'vasttrafik' in operator or \
           'västtrafik' in network or 'vasttrafik' in network:
            vasttrafik_stops.append(stop)
        else:
            other_stops.append(stop)

    return vasttrafik_stops, other_stops


def main():
    """Main function"""
    print("=" * 70)
    print("OpenStreetMap Bus Stop Fetcher")
    print("Alternative method using OSM Overpass API (no API key needed)")
    print("=" * 70)
    print("\nData source: OpenStreetMap (community-maintained)")
    print("Coverage: Västra Götalands län, Sweden")
    print("=" * 70)

    # Build query
    query = build_overpass_query(BOUNDING_BOX)

    # Execute query
    data = query_overpass(query)
    if not data:
        return

    # Extract stops
    print("\nExtracting stop information...")
    all_stops = extract_stops_from_osm(data)
    print(f"✓ Extracted {len(all_stops)} stops from OSM data")

    # Filter by operator
    vasttrafik_stops, other_stops = filter_by_operator(all_stops)

    print(f"\n  - Västtrafik operated: {len(vasttrafik_stops)}")
    print(f"  - Other operators: {len(other_stops)}")

    # Save all stops (you can choose to save only Västtrafik if preferred)
    stops_to_save = all_stops  # Change to vasttrafik_stops if you want only Västtrafik

    print(f"\n{'=' * 70}")
    print(f"Saving {len(stops_to_save)} stops to {OUTPUT_FILE}...")
    print(f"{'=' * 70}")

    output_data = {
        'total_stops': len(stops_to_save),
        'vasttrafik_stops': len(vasttrafik_stops),
        'other_stops': len(other_stops),
        'source': 'OpenStreetMap via Overpass API',
        'region': 'Västra Götalands län',
        'bounding_box': {
            'min_lat': BOUNDING_BOX[0],
            'min_lon': BOUNDING_BOX[1],
            'max_lat': BOUNDING_BOX[2],
            'max_lon': BOUNDING_BOX[3]
        },
        'license': 'ODbL (OpenStreetMap)',
        'stops': stops_to_save
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"✓ Saved to {OUTPUT_FILE}\n")

    # Show samples
    if stops_to_save:
        print("Sample Västtrafik stops:")
        count = 0
        for stop in stops_to_save:
            if 'västtrafik' in stop.get('operator', '').lower() or \
               'vasttrafik' in stop.get('operator', '').lower():
                print(f"  • {stop['name']} ({stop['latitude']}, {stop['longitude']})")
                print(f"    Operator: {stop.get('operator', 'N/A')}, Type: {stop['stop_type']}")
                count += 1
                if count >= 10:
                    break

        # Statistics
        print(f"\nStatistics:")
        print(f"  Total stops: {len(stops_to_save)}")

        # Count by type
        types = {}
        for stop in stops_to_save:
            stop_type = stop.get('stop_type', 'unknown')
            types[stop_type] = types.get(stop_type, 0) + 1

        print("\n  Stop types:")
        for stop_type, count in sorted(types.items(), key=lambda x: x[1], reverse=True):
            print(f"    - {stop_type}: {count}")

        # Count operators
        operators = {}
        for stop in stops_to_save:
            operator = stop.get('operator', 'Unknown')
            if operator:
                operators[operator] = operators.get(operator, 0) + 1

        if operators:
            print("\n  Top operators:")
            for operator, count in sorted(operators.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"    - {operator}: {count}")

    print("\n" + "=" * 70)
    print("Note: OSM data is community-maintained and may not be 100% complete.")
    print("For official data, use the GTFS method (fetch_bus_stops_gtfs.py)")
    print("=" * 70)


if __name__ == "__main__":
    main()
