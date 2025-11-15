#!/usr/bin/env python3
"""
Fast CTF Solver - Uses concurrent requests for maximum speed
Supports multiple input formats for stops
"""

import requests
import json
import time
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Optional
import threading

# Configuration
CTF_URL = "http://challs.crate.nu:41242/cpos.php"
STOPS_FILE = "stops[1].txt"  # Or bus_stops.json
MAX_WORKERS = 50  # Number of concurrent threads
TIMEOUT = 5  # Request timeout in seconds

# Thread-safe counters
lock = threading.Lock()
attempts = 0
found = False
close_positions = []


def test_position(lat: float, lon: float, name: str = "", index: int = 0) -> Optional[dict]:
    """Test a single position"""
    global attempts, found, close_positions

    if found:
        return None

    pos_str = f"{lat},{lon}"

    try:
        data = {"pos": pos_str}
        response = requests.post(CTF_URL, data=data, timeout=TIMEOUT)

        with lock:
            attempts += 1

        if response.status_code == 200:
            content = response.text.lower()

            # Check for flag
            if any(flag in content for flag in ["flag{", "ctf{", "crew{", "crate{"]):
                with lock:
                    if not found:
                        found = True
                        print(f"\n{'='*70}")
                        print(f"🎉 FLAG FOUND!")
                        print(f"{'='*70}")
                        print(f"Position: {lat},{lon}")
                        print(f"Name: {name}")
                        print(f"Index: {index}")
                        print(f"\n{response.text}\n")
                        print(f"{'='*70}\n")
                        return {"lat": lat, "lon": lon, "name": name, "response": response.text}

            # Check for "getting there"
            try:
                result = response.json()
                error = result.get("error", "")
                if "getting there" in error.lower():
                    with lock:
                        close_positions.append((lat, lon, name))
                        print(f"  [CLOSE] {pos_str} - {name}")
            except:
                pass

        # Progress indicator
        with lock:
            if attempts % 100 == 0:
                print(f"  Progress: {attempts} tested, {len(close_positions)} close", end='\r')

        return None

    except Exception as e:
        return None


def load_stops_from_txt(filename: str) -> List[Tuple[float, float, str]]:
    """Load stops from text file - supports multiple formats"""
    stops = []

    print(f"Loading stops from {filename}...")

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # Try to parse different formats:
                # Format 1: "lat,lon"
                # Format 2: "lat,lon,name"
                # Format 3: "name,lat,lon"
                # Format 4: JSON per line

                try:
                    # Try JSON first
                    if line.startswith('{'):
                        data = json.loads(line)
                        lat = float(data.get('latitude') or data.get('lat') or data.get('y'))
                        lon = float(data.get('longitude') or data.get('lon') or data.get('x'))
                        name = data.get('name', f'Stop {i}')
                        stops.append((lat, lon, name))
                        continue

                    # Try CSV format
                    parts = line.split(',')
                    if len(parts) >= 2:
                        # Try lat,lon first
                        try:
                            lat = float(parts[0].strip())
                            lon = float(parts[1].strip())
                            name = parts[2].strip() if len(parts) > 2 else f'Stop {i}'

                            # Sanity check for Swedish coordinates
                            if 55 <= lat <= 70 and 10 <= lon <= 25:
                                stops.append((lat, lon, name))
                            else:
                                # Maybe it's lon,lat
                                lat, lon = lon, lat
                                if 55 <= lat <= 70 and 10 <= lon <= 25:
                                    stops.append((lat, lon, name))
                        except ValueError:
                            continue

                    # Try tab-separated
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        try:
                            lat = float(parts[0].strip())
                            lon = float(parts[1].strip())
                            name = parts[2].strip() if len(parts) > 2 else f'Stop {i}'
                            if 55 <= lat <= 70 and 10 <= lon <= 25:
                                stops.append((lat, lon, name))
                        except ValueError:
                            continue

                except Exception as e:
                    if i <= 5:  # Only show errors for first few lines
                        print(f"  Skipping line {i}: {e}")
                    continue

        print(f"✓ Loaded {len(stops)} stops")
        return stops

    except FileNotFoundError:
        print(f"✗ File not found: {filename}")
        return []


def load_stops_from_json(filename: str) -> List[Tuple[float, float, str]]:
    """Load stops from JSON file"""
    stops = []

    print(f"Loading stops from {filename}...")

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

        stop_list = data.get('stops', [])

        for stop in stop_list:
            lat = stop.get('latitude') or stop.get('lat')
            lon = stop.get('longitude') or stop.get('lon')
            name = stop.get('name') or stop.get('stop_name', 'Unknown')

            if lat and lon:
                stops.append((float(lat), float(lon), name))

        print(f"✓ Loaded {len(stops)} stops")
        return stops

    except Exception as e:
        print(f"✗ Error loading JSON: {e}")
        return []


def solve_fast(stops: List[Tuple[float, float, str]]):
    """Solve using concurrent requests"""
    global attempts, found

    print(f"\n{'='*70}")
    print(f"Starting fast CTF solver")
    print(f"{'='*70}")
    print(f"Total stops: {len(stops)}")
    print(f"Max workers: {MAX_WORKERS}")
    print(f"{'='*70}\n")

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks
        futures = []
        for i, (lat, lon, name) in enumerate(stops):
            future = executor.submit(test_position, lat, lon, name, i)
            futures.append(future)

        # Process results as they complete
        for future in as_completed(futures):
            if found:
                # Cancel remaining tasks
                for f in futures:
                    f.cancel()
                break

            result = future.result()
            if result:
                # Found the flag!
                elapsed = time.time() - start_time
                print(f"\n✓ Solved in {elapsed:.2f} seconds after {attempts} attempts")
                return result

    elapsed = time.time() - start_time
    print(f"\n{'='*70}")
    print(f"Completed in {elapsed:.2f} seconds")
    print(f"Total attempts: {attempts}")
    print(f"Rate: {attempts/elapsed:.2f} requests/sec")
    print(f"Close positions: {len(close_positions)}")
    print(f"{'='*70}")

    if close_positions:
        print(f"\nTop 20 close positions:")
        for lat, lon, name in close_positions[:20]:
            print(f"  {lat},{lon} - {name}")

    return None


def main():
    """Main function"""
    import os

    # Try to load stops from multiple sources
    stops = []

    # Try stops[1].txt first
    if os.path.exists(STOPS_FILE):
        stops = load_stops_from_txt(STOPS_FILE)

    # Fallback to bus_stops.json
    if not stops and os.path.exists("bus_stops.json"):
        print(f"\n{STOPS_FILE} not found, trying bus_stops.json...")
        stops = load_stops_from_json("bus_stops.json")

    # Fallback to bus_stops_osm.json
    if not stops and os.path.exists("bus_stops_osm.json"):
        print(f"\nTrying bus_stops_osm.json...")
        stops = load_stops_from_json("bus_stops_osm.json")

    if not stops:
        print("\n✗ No stops found!")
        print(f"\nPlease create one of these files:")
        print(f"  1. {STOPS_FILE} - Text file with coordinates")
        print(f"  2. bus_stops.json - JSON file with stops")
        print(f"\nSupported formats for {STOPS_FILE}:")
        print(f"  - lat,lon")
        print(f"  - lat,lon,name")
        print(f"  - JSON objects per line")
        sys.exit(1)

    # Solve!
    result = solve_fast(stops)

    if result:
        # Save result
        with open("ctf_flag.txt", 'w', encoding='utf-8') as f:
            f.write(result['response'])
        print(f"\n✓ Flag saved to ctf_flag.txt")
    else:
        print(f"\n❌ Flag not found")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n⚠ Interrupted by user")
        print(f"Tested {attempts} positions before stopping")
        if close_positions:
            print(f"Found {len(close_positions)} close positions")
