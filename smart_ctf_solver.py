#!/usr/bin/env python3
"""
Smart CTF Solver with multiple strategies
- Tests coordinates from bus_stops.json
- Generates coordinate grid for Gothenburg area
- Tests various formats and patterns
"""

import requests
import json
import time
import sys
from typing import List, Dict, Optional
from itertools import product

# Configuration
CTF_URL = "http://challs.crate.nu:41242/cpos.php"
BUS_STOPS_FILE = "bus_stops.json"

class SmartCTFSolver:
    """Advanced solver with multiple strategies"""

    def __init__(self, ctf_url: str):
        self.ctf_url = ctf_url
        self.session = requests.Session()
        self.attempts = 0
        self.found_flags = []

    def test_position(self, pos: str, context: str = "") -> Optional[Dict]:
        """Test a position and return detailed results"""
        self.attempts += 1

        try:
            data = {"pos": pos}
            response = self.session.post(
                self.ctf_url,
                data=data,
                timeout=10,
                allow_redirects=True
            )

            content = response.text
            status = response.status_code

            # Analyze response
            is_interesting = False
            is_flag = False

            # Flag patterns
            flag_patterns = ["flag{", "ctf{", "crew{", "crate{", "FLAG{", "CTF{"]
            success_words = ["correct", "success", "congratulations", "you found",
                           "well done", "rätt", "bra", "grattis", "flagga"]

            # Check for flags
            for pattern in flag_patterns:
                if pattern.lower() in content.lower():
                    is_flag = True
                    is_interesting = True
                    break

            # Check for success indicators
            for word in success_words:
                if word in content.lower():
                    is_interesting = True
                    break

            # Check for non-empty or non-default responses
            if len(content) > 100 or status != 200:
                is_interesting = True

            # Log interesting responses
            if is_interesting or is_flag:
                result = {
                    "position": pos,
                    "context": context,
                    "status": status,
                    "response": content,
                    "is_flag": is_flag,
                    "attempt": self.attempts
                }

                if is_flag:
                    print(f"\n{'='*70}")
                    print(f"🎉 FLAG FOUND!")
                    print(f"{'='*70}")
                    print(f"Position: {pos}")
                    print(f"Context: {context}")
                    print(f"Response:\n{content}")
                    print(f"{'='*70}\n")
                    self.found_flags.append(result)
                else:
                    print(f"  [Interesting] {pos}: {status} - {content[:200]}")

                return result

            # Quiet progress
            if self.attempts % 100 == 0:
                print(f"  Progress: {self.attempts} positions tested...")

            return None

        except requests.exceptions.RequestException as e:
            if self.attempts % 50 == 0:
                print(f"  ✗ Network error at attempt {self.attempts}: {e}")
            return None

    def strategy_bus_stops_json(self) -> bool:
        """Strategy 1: Test from bus_stops.json"""
        print("\n=== Strategy 1: Testing bus stops from JSON ===\n")

        try:
            with open(BUS_STOPS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"✗ {BUS_STOPS_FILE} not found, skipping this strategy")
            return False

        stops = data.get("stops", [])
        print(f"Loaded {len(stops)} stops\n")

        for i, stop in enumerate(stops, 1):
            name = stop.get("name", "Unknown")
            lat = stop.get("latitude")
            lon = stop.get("longitude")
            stop_id = stop.get("id") or stop.get("gid")

            if not lat or not lon:
                continue

            # Test various formats
            formats = [
                (f"{lat},{lon}", f"{name} - standard"),
                (f"{lat:.6f},{lon:.6f}", f"{name} - 6 decimals"),
                (f"{lat:.4f},{lon:.4f}", f"{name} - 4 decimals"),
                (f"{lon},{lat}", f"{name} - reversed"),
                (name, f"{name} - name only"),
                (str(stop_id) if stop_id else None, f"{name} - ID"),
            ]

            for fmt, ctx in formats:
                if fmt is None:
                    continue
                self.test_position(fmt, ctx)
                time.sleep(0.05)

            if self.found_flags:
                return True

        return bool(self.found_flags)

    def strategy_coordinate_grid(self) -> bool:
        """Strategy 2: Grid search of Gothenburg area"""
        print("\n=== Strategy 2: Coordinate grid search ===\n")

        # Gothenburg area bounds
        lat_min, lat_max = 57.60, 57.80
        lon_min, lon_max = 11.85, 12.10

        # Fine grid
        lat_step = 0.01  # ~1km
        lon_step = 0.01

        lat_points = []
        lat = lat_min
        while lat <= lat_max:
            lat_points.append(lat)
            lat += lat_step

        lon_points = []
        lon = lon_min
        while lon <= lon_max:
            lon_points.append(lon)
            lon += lon_step

        total = len(lat_points) * len(lon_points)
        print(f"Testing {total} grid points...\n")

        count = 0
        for lat, lon in product(lat_points, lon_points):
            count += 1

            formats = [
                f"{lat:.4f},{lon:.4f}",
                f"{lat:.6f},{lon:.6f}",
            ]

            for fmt in formats:
                self.test_position(fmt, f"Grid {count}/{total}")
                time.sleep(0.05)

                if self.found_flags:
                    return True

        return bool(self.found_flags)

    def strategy_known_locations(self) -> bool:
        """Strategy 3: Test well-known Gothenburg locations"""
        print("\n=== Strategy 3: Known Gothenburg landmarks ===\n")

        known_locations = [
            ("57.7065,11.9666", "Brunnsparken"),
            ("57.7089,11.9733", "Centralstationen"),
            ("57.6878,11.9793", "Korsvägen"),
            ("57.7047,11.9614", "Domkyrkan"),
            ("57.6969,11.9865", "Järntorget"),
            ("57.7100,11.9709", "Nordstan"),
            ("57.6971,12.0037", "Linnéplatsen"),
            ("57.6889,11.9795", "Chalmers"),
            ("57.6970,12.0400", "Scandinavium"),
            ("57.7215,11.9408", "Hisingen"),
        ]

        for coord, name in known_locations:
            print(f"Testing: {name}")

            # Try multiple formats
            parts = coord.split(',')
            lat, lon = parts[0], parts[1]

            formats = [
                coord,
                f"{lat}, {lon}",
                f"{lon},{lat}",
                name,
            ]

            for fmt in formats:
                self.test_position(fmt, name)
                time.sleep(0.1)

                if self.found_flags:
                    return True

        return bool(self.found_flags)

    def solve(self):
        """Run all strategies"""
        print("="*70)
        print("Smart Buslätt CTF Solver")
        print("="*70)

        strategies = [
            ("Bus Stops from JSON", self.strategy_bus_stops_json),
            ("Known Locations", self.strategy_known_locations),
            ("Coordinate Grid", self.strategy_coordinate_grid),
        ]

        for name, strategy in strategies:
            print(f"\n{'='*70}")
            print(f"Running: {name}")
            print(f"{'='*70}")

            try:
                if strategy():
                    print(f"\n✓ Flag found using strategy: {name}")
                    break
            except KeyboardInterrupt:
                print("\n\n⚠ Interrupted by user")
                break
            except Exception as e:
                print(f"\n✗ Strategy failed: {e}")
                continue

        # Summary
        print(f"\n{'='*70}")
        print("Summary")
        print(f"{'='*70}")
        print(f"Total attempts: {self.attempts}")
        print(f"Flags found: {len(self.found_flags)}")

        if self.found_flags:
            print("\n🎉 FLAGS:")
            for flag in self.found_flags:
                print(f"\nPosition: {flag['position']}")
                print(f"Context: {flag['context']}")
                print(f"Response:\n{flag['response']}\n")

            # Save results
            with open("ctf_solution.json", 'w', encoding='utf-8') as f:
                json.dump(self.found_flags, f, indent=2, ensure_ascii=False)
            print("✓ Results saved to ctf_solution.json")
        else:
            print("\n❌ No flags found")


def main():
    solver = SmartCTFSolver(CTF_URL)
    solver.solve()


if __name__ == "__main__":
    main()
