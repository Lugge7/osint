#!/usr/bin/env python3
"""
Adaptive CTF Solver - Uses feedback from the endpoint
Narrows down search when getting "Getting there" responses
"""

import requests
import json
import time
import sys
from typing import List, Dict, Optional, Tuple

# Configuration
CTF_URL = "http://challs.crate.nu:41242/cpos.php"
BUS_STOPS_FILE = "bus_stops.json"

class AdaptiveSolver:
    """Solver that adapts based on CTF endpoint feedback"""

    def __init__(self, ctf_url: str):
        self.ctf_url = ctf_url
        self.session = requests.Session()
        self.attempts = 0
        self.close_positions = []  # Positions that got "Getting there"

    def test_position(self, lat: float, lon: float, context: str = "") -> Optional[str]:
        """Test a position and return the response"""
        self.attempts += 1

        pos_str = f"{lat},{lon}"

        try:
            data = {"pos": pos_str}
            response = self.session.post(
                self.ctf_url,
                data=data,
                timeout=10
            )

            if response.status_code == 200:
                try:
                    result = response.json()

                    # Check for flag
                    if "flag" in result or "FLAG" in result:
                        print(f"\n{'='*70}")
                        print(f"🎉 FLAG FOUND!")
                        print(f"{'='*70}")
                        print(f"Position: {lat},{lon}")
                        print(f"Context: {context}")
                        print(f"Response: {json.dumps(result, indent=2)}")
                        print(f"{'='*70}\n")
                        return "FLAG"

                    # Check if getting close
                    error = result.get("error", "")
                    if "getting there" in error.lower():
                        print(f"  [CLOSE!] {pos_str} - {error}")
                        self.close_positions.append((lat, lon, context))
                        return "CLOSE"
                    elif "wrong format" in error.lower():
                        return "ERROR"
                    else:
                        # Unknown response
                        if self.attempts % 100 == 0:
                            print(f"  [{self.attempts}] {pos_str}: {error}")
                        return "OTHER"

                except json.JSONDecodeError:
                    # Not JSON, might be the flag in HTML
                    content = response.text.lower()
                    if any(pattern in content for pattern in ["flag{", "crew{", "crate{", "ctf{"]):
                        print(f"\n{'='*70}")
                        print(f"🎉 FLAG FOUND!")
                        print(f"{'='*70}")
                        print(f"Position: {lat},{lon}")
                        print(f"Response:\n{response.text}")
                        print(f"{'='*70}\n")
                        return "FLAG"

            return None

        except requests.exceptions.RequestException as e:
            if self.attempts % 50 == 0:
                print(f"  ✗ Network error: {e}")
            return None

    def refine_search(self, lat: float, lon: float, radius: float = 0.001, steps: int = 20):
        """Refine search around a promising coordinate"""
        print(f"\n  🔍 Refining search around {lat},{lon} (radius: {radius})")

        step_size = radius / steps

        for lat_offset in range(-steps, steps + 1):
            for lon_offset in range(-steps, steps + 1):
                test_lat = lat + (lat_offset * step_size)
                test_lon = lon + (lon_offset * step_size)

                result = self.test_position(test_lat, test_lon, f"Refining around {lat},{lon}")

                if result == "FLAG":
                    return True

                time.sleep(0.05)

        return False

    def solve_from_bus_stops(self):
        """Test all bus stops and refine around close ones"""
        print("\n=== Loading bus stops ===\n")

        try:
            with open(BUS_STOPS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"✗ {BUS_STOPS_FILE} not found")
            return False

        stops = data.get("stops", [])
        print(f"Loaded {len(stops)} stops\n")

        # Phase 1: Test all stops
        print("=== Phase 1: Testing all bus stops ===\n")

        for i, stop in enumerate(stops, 1):
            name = stop.get("name", "Unknown")
            lat = stop.get("latitude")
            lon = stop.get("longitude")

            if not lat or not lon:
                continue

            if i % 50 == 0:
                print(f"Progress: {i}/{len(stops)} ({100*i/len(stops):.1f}%)")

            result = self.test_position(lat, lon, name)

            if result == "FLAG":
                return True

            time.sleep(0.05)

        # Phase 2: Refine around close positions
        if self.close_positions:
            print(f"\n=== Phase 2: Refining {len(self.close_positions)} promising positions ===\n")

            for lat, lon, context in self.close_positions:
                print(f"\nRefining: {context}")

                # Try progressively smaller radii
                for radius in [0.001, 0.0005, 0.0001]:
                    if self.refine_search(lat, lon, radius, steps=10):
                        return True

        return False

    def solve_grid_search(self, lat_min=57.60, lat_max=57.80, lon_min=11.85, lon_max=12.10):
        """Grid search with adaptive refinement"""
        print("\n=== Grid Search ===\n")

        # Coarse grid first
        lat_step = 0.01
        lon_step = 0.01

        lat = lat_min
        while lat <= lat_max:
            lon = lon_min
            while lon <= lon_max:
                result = self.test_position(lat, lon, "Grid search")

                if result == "FLAG":
                    return True

                lon += lon_step
                time.sleep(0.05)

            lat += lat_step
            print(f"  Grid progress: {lat:.4f}/{lat_max:.4f}")

        # Refine close positions
        if self.close_positions:
            print(f"\n  Found {len(self.close_positions)} close positions, refining...")
            for lat, lon, context in self.close_positions:
                if self.refine_search(lat, lon, radius=0.005, steps=15):
                    return True

        return False


def main():
    print("="*70)
    print("Adaptive Buslätt CTF Solver")
    print("="*70)

    solver = AdaptiveSolver(CTF_URL)

    # Try bus stops first
    import os
    if os.path.exists(BUS_STOPS_FILE):
        if solver.solve_from_bus_stops():
            print("\n✓ Solved using bus stops!")
            return
    else:
        print(f"\n⚠ {BUS_STOPS_FILE} not found, will use grid search")

    # Fallback to grid search
    print("\nTrying grid search...")
    if solver.solve_grid_search():
        print("\n✓ Solved using grid search!")
        return

    # Summary
    print(f"\n{'='*70}")
    print("Summary")
    print(f"{'='*70}")
    print(f"Total attempts: {solver.attempts}")
    print(f"Close positions found: {len(solver.close_positions)}")

    if solver.close_positions:
        print("\nPositions that were close:")
        for lat, lon, ctx in solver.close_positions[:10]:
            print(f"  {lat},{lon} - {ctx}")


if __name__ == "__main__":
    main()
