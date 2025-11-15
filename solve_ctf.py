#!/usr/bin/env python3
"""
CTF Solver for Buslätt Challenge
Tests all bus stop coordinates against the CTF endpoint
"""

import requests
import json
import time
import sys
from typing import List, Dict, Optional

# Configuration
CTF_URL = "http://challs.crate.nu:41242/cpos.php"
BUS_STOPS_FILE = "bus_stops.json"
OUTPUT_FILE = "ctf_results.txt"

class CTFSolver:
    """Solver for the Buslätt CTF challenge"""

    def __init__(self, ctf_url: str):
        self.ctf_url = ctf_url
        self.session = requests.Session()
        self.attempts = 0
        self.success = False

    def test_position(self, pos: str, stop_info: Dict = None) -> Optional[str]:
        """Test a position against the CTF endpoint"""
        self.attempts += 1

        try:
            # Submit the position
            data = {"pos": pos}
            response = self.session.post(
                self.ctf_url,
                data=data,
                timeout=10,
                allow_redirects=True
            )

            # Check response
            content = response.text.lower()

            # Look for common CTF flag patterns or success indicators
            flag_indicators = [
                "flag{", "ctf{", "crew{", "crate{",
                "correct", "success", "congratulations",
                "you found", "well done", "rätt"  # Swedish for "correct"
            ]

            if any(indicator in content for indicator in flag_indicators):
                print(f"\n{'='*70}")
                print(f"🎉 POTENTIAL FLAG FOUND!")
                print(f"{'='*70}")
                print(f"Position tested: {pos}")
                if stop_info:
                    print(f"Stop info: {stop_info}")
                print(f"\nResponse ({response.status_code}):")
                print(response.text)
                print(f"{'='*70}\n")
                self.success = True
                return response.text

            # Print progress for interesting responses
            if response.status_code != 200 or len(response.text) > 50:
                print(f"  [{self.attempts}] {pos[:50]}: {response.status_code} - {response.text[:100]}")

            return None

        except requests.exceptions.RequestException as e:
            print(f"  ✗ Error testing {pos}: {e}")
            return None

    def test_formats(self, stop: Dict) -> Optional[str]:
        """Test different coordinate formats for a stop"""
        lat = stop.get("latitude")
        lon = stop.get("longitude")
        name = stop.get("name")
        stop_id = stop.get("id") or stop.get("gid")

        if not lat or not lon:
            return None

        # Try different position formats
        formats = [
            # Coordinate formats
            f"{lat},{lon}",
            f"{lat}, {lon}",
            f"{lon},{lat}",  # Sometimes lon,lat order
            f"{lon}, {lat}",
            f"({lat},{lon})",
            f"({lat}, {lon})",
            f"{lat:.6f},{lon:.6f}",
            f"{lat:.4f},{lon:.4f}",

            # Stop ID formats
            str(stop_id) if stop_id else None,

            # Name format
            name,
        ]

        for fmt in formats:
            if fmt is None:
                continue

            result = self.test_position(fmt, stop)
            if result:
                return result

            time.sleep(0.1)  # Rate limiting

        return None

    def solve_from_json(self, json_file: str):
        """Load bus stops from JSON and test them"""
        print(f"Loading bus stops from {json_file}...")

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"✗ File not found: {json_file}")
            print("\nPlease run fetch_bus_stops_v2.py first to generate the bus stops data.")
            sys.exit(1)

        stops = data.get("stops", [])
        total = len(stops)

        print(f"Loaded {total} bus stops")
        print(f"Testing against: {self.ctf_url}")
        print(f"{'='*70}\n")

        # Test each stop
        for i, stop in enumerate(stops, 1):
            name = stop.get("name", "Unknown")
            print(f"\n[{i}/{total}] Testing: {name}")

            result = self.test_formats(stop)

            if result:
                # Found the flag!
                with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                    f.write(f"Stop: {stop}\n\n")
                    f.write(f"Response:\n{result}\n")
                print(f"\n✓ Results saved to {OUTPUT_FILE}")
                return True

            # Progress indicator
            if i % 10 == 0:
                print(f"\n  Progress: {i}/{total} ({100*i/total:.1f}%)")

        print(f"\n{'='*70}")
        print(f"Completed testing {total} stops")
        print(f"Total attempts: {self.attempts}")
        print(f"{'='*70}")

        return self.success

    def test_manual_coordinates(self, coordinates: List[str]):
        """Test a list of manual coordinates"""
        print(f"Testing {len(coordinates)} manual coordinates...")
        print(f"{'='*70}\n")

        for i, coord in enumerate(coordinates, 1):
            print(f"[{i}/{len(coordinates)}] Testing: {coord}")
            result = self.test_position(coord)

            if result:
                print(f"\n✓ Found with coordinate: {coord}")
                return True

            time.sleep(0.1)

        return False


def main():
    """Main function"""
    print("="*70)
    print("Buslätt CTF Solver")
    print("="*70)
    print()

    solver = CTFSolver(CTF_URL)

    # Check if we have bus stops JSON file
    import os
    if os.path.exists(BUS_STOPS_FILE):
        print(f"Found {BUS_STOPS_FILE}, testing all stops...")
        success = solver.solve_from_json(BUS_STOPS_FILE)
    else:
        print(f"⚠ {BUS_STOPS_FILE} not found.")
        print("\nTo use this solver:")
        print("1. Run: python fetch_bus_stops_v2.py")
        print("2. Wait for bus_stops.json to be generated")
        print("3. Run this script again")
        print()
        print("Alternatively, you can test manual coordinates:")

        # Test some common Gothenburg bus stops as examples
        manual_coords = [
            "57.7065,11.9666",  # Brunnsparken
            "57.7089,11.9733",  # Centralstationen
            "57.6878,11.9793",  # Korsvägen
        ]

        test_manual = input("\nTest some sample coordinates? (y/n): ").strip().lower()
        if test_manual == 'y':
            success = solver.test_manual_coordinates(manual_coords)
        else:
            sys.exit(0)

    if success:
        print("\n🎉 CTF SOLVED!")
    else:
        print("\n❌ No flag found. Try:")
        print("  1. Verify the CTF endpoint is correct")
        print("  2. Check if more stops need to be tested")
        print("  3. Try different coordinate formats")


if __name__ == "__main__":
    main()
