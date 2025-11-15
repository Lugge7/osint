#!/usr/bin/env python3
"""
Test connection to Västtrafik API and verify credentials
"""

import requests
import sys

API_KEY = "RXFrWXB0azVuNm43Slg5VmdmbGhkSnl3cnVrYTpNU0NqbEswaFNfa0dJd1RjYmlKSHRaVDNxRXNh"

def test_dns_resolution():
    """Test if we can resolve Västtrafik domains"""
    import socket

    domains = [
        "api.vasttrafik.se",
        "ext-api.vasttrafik.se",
        "developer.vasttrafik.se"
    ]

    print("=== Testing DNS Resolution ===\n")
    all_ok = True

    for domain in domains:
        try:
            ip = socket.gethostbyname(domain)
            print(f"✓ {domain} resolves to {ip}")
        except socket.gaierror:
            print(f"✗ {domain} - DNS resolution failed")
            all_ok = False

    return all_ok


def test_token_endpoint(token_url):
    """Test if we can reach the token endpoint"""
    print(f"\n=== Testing Token Endpoint ===")
    print(f"URL: {token_url}\n")

    headers = {
        "Authorization": f"Basic {API_KEY}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "client_credentials"
    }

    try:
        response = requests.post(token_url, headers=headers, data=data, timeout=10)

        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}\n")

        if response.status_code == 200:
            token_data = response.json()
            print("✓ Authentication successful!")
            print(f"  Token Type: {token_data.get('token_type')}")
            print(f"  Expires In: {token_data.get('expires_in')} seconds")
            print(f"  Scope: {token_data.get('scope', 'N/A')}")
            return True
        else:
            print(f"✗ Authentication failed")
            print(f"  Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"✗ Connection failed: {e}")
        return False


def main():
    print("=" * 70)
    print("Västtrafik API Connection Test")
    print("=" * 70)
    print()

    # Test DNS
    dns_ok = test_dns_resolution()

    if not dns_ok:
        print("\n⚠ DNS resolution issues detected.")
        print("  This may indicate:")
        print("  - Network connectivity problems")
        print("  - Firewall blocking the domains")
        print("  - Geographic restrictions")
        print("  - VPN or proxy configuration needed")
        print("\n  Try running this script from a different network.")

    # Test token endpoints
    token_urls = [
        "https://api.vasttrafik.se/token",
    ]

    auth_ok = False
    for url in token_urls:
        if test_token_endpoint(url):
            auth_ok = True
            break

    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"DNS Resolution: {'✓ OK' if dns_ok else '✗ FAILED'}")
    print(f"Authentication: {'✓ OK' if auth_ok else '✗ FAILED'}")

    if dns_ok and auth_ok:
        print("\n✓ All tests passed! You can run fetch_bus_stops_v2.py")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
