# Västtrafik Bus Stop Coordinate Fetcher

Fetch all bus stop coordinates from the Västtrafik API (Swedish public transport system covering Gothenburg and surrounding areas).

## Overview

This project provides tools to extract comprehensive bus stop data including coordinates from Västtrafik's public API. It supports multiple API versions and includes robust error handling and troubleshooting capabilities.

## Features

- **Multi-version support**: Works with both v2 and v4 APIs
- **OAuth2 authentication** with automatic token refresh
- **Multiple search strategies**:
  - Direct "all stops" endpoint (v2 API)
  - Text-based search using Swedish alphabet and common terms
  - Grid-based coordinate search for v4 API
- **Automatic deduplication** of stops
- **JSON export** with coordinates and metadata
- **Connection testing** and diagnostics

## Requirements

- Python 3.6 or higher
- `requests` library

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

1. **Test your connection** first:
```bash
python test_connection.py
```

2. **Run the fetcher**:
```bash
python fetch_bus_stops_v2.py
```

3. **Check the output**:
```bash
cat bus_stops.json
```

## CTF Challenge Solver

This repository includes solvers for the **Buslätt** CTF challenge (http://challs.crate.nu:41242/).

### Quick Solve

```bash
# Option 1: Use bus stops data (most accurate)
python fetch_bus_stops_v2.py  # Get all bus stops first
python adaptive_ctf_solver.py  # Solve the CTF

# Option 2: Smart solver with multiple strategies
python smart_ctf_solver.py

# Option 3: Basic solver
python solve_ctf.py
```

### CTF Solver Scripts

#### `adaptive_ctf_solver.py` (Recommended for CTF)
- Uses endpoint feedback ("Getting there" responses)
- Automatically refines search around promising coordinates
- Two-phase approach: broad search + focused refinement
- Works with or without bus_stops.json

#### `smart_ctf_solver.py`
- Multi-strategy solver
- Tests bus stops, known locations, and coordinate grids
- Comprehensive coverage

#### `solve_ctf.py`
- Basic solver that tests all coordinates from bus_stops.json
- Multiple format testing (lat,lon / lon,lat / names / IDs)

### How the CTF Works

The challenge shows a Västtrafik bus stop sign and asks for the position where the photo was taken.

- **Endpoint**: POST to `/cpos.php` with parameter `pos`
- **Feedback**: Returns JSON with error messages
  - `"Getting there"` = close but not exact
  - `"Wrong format of position"` = invalid input
  - Success returns the flag
- **Format**: Coordinates as `"latitude,longitude"`

## Scripts

### `fetch_bus_stops_v2.py` (Recommended)

The main script with support for v2 and v4 APIs. Features:
- Configurable API version
- Multiple fallback strategies
- Better error handling
- Works with older v2 API (more reliable)

**Configuration**: Edit the `CONFIG` dictionary at the top of the file:
```python
CONFIG = {
    "api_key": "YOUR_API_KEY_HERE",
    "version": "v2",  # or "v4"
    "output_file": "bus_stops.json"
}
```

### `fetch_bus_stops.py`

Original v4-focused implementation with:
- Grid search covering Gothenburg region (57.4-58.0°N, 11.5-12.5°E)
- Comprehensive text search
- Detailed progress reporting

### `test_connection.py`

Diagnostic tool to verify:
- DNS resolution for Västtrafik domains
- API endpoint accessibility
- OAuth2 authentication
- Credential validity

## API Versions

### v2 API (Recommended)
- **Token URL**: `https://api.vasttrafik.se/token`
- **Base URL**: `https://api.vasttrafik.se/bin/rest.exe/v2`
- **Advantage**: Has `location.allstops` endpoint for complete data
- **Format**: Returns `StopLocation` objects

### v4 API
- **Token URL**: `https://api.vasttrafik.se/token`
- **Base URL**: `https://ext-api.vasttrafik.se/pr/v4`
- **Endpoints**: `/locations/by-text`, `/locations/by-coordinates`
- **Format**: Returns location objects with more detailed metadata

## Output Format

### v2 API Output
```json
{
  "total_stops": 1234,
  "api_version": "v2",
  "fetched_at": "2025-11-15 14:30:00",
  "stops": [
    {
      "id": "9021014001960000",
      "name": "Brunnsparken",
      "latitude": 57.7065,
      "longitude": 11.9666,
      "track": "",
      "api_version": "v2"
    }
  ]
}
```

### v4 API Output
```json
{
  "total_stops": 1234,
  "api_version": "v4",
  "fetched_at": "2025-11-15 14:30:00",
  "stops": [
    {
      "gid": "9021014001960000",
      "name": "Brunnsparken",
      "latitude": 57.7065,
      "longitude": 11.9666,
      "type": "stoparea",
      "municipality": "Göteborg",
      "api_version": "v4"
    }
  ]
}
```

## Getting API Credentials

1. Visit [Västtrafik Developer Portal](https://developer.vasttrafik.se)
2. Create an account and log in
3. Create a new application
4. Subscribe to "Planera Resa v4" or "Reseplaneraren v2" API
5. Copy your API key (format: `client_id:client_secret`)
6. Base64 encode the credentials or use them directly

The API key format should be: `Base64(client_id:client_secret)`

## Troubleshooting

### DNS Resolution Failure

**Error**: `DNS resolution failure` or `503 Service Unavailable`

**Possible causes**:
- Network connectivity issues
- Firewall blocking api.vasttrafik.se domain
- Geographic restrictions
- VPN/proxy configuration needed

**Solutions**:
1. Run `python test_connection.py` to diagnose
2. Try from a different network
3. Check firewall settings
4. Verify internet connectivity: `ping 8.8.8.8`

### Authentication Failed (401)

**Error**: `invalid_client` or `401 Unauthorized`

**Solutions**:
1. Verify your API key is correct
2. Check you have an active subscription at developer.vasttrafik.se
3. Ensure you're using the right API version (v2 vs v4)
4. Try regenerating your API credentials

### No Stops Found

**Possible causes**:
- Authentication succeeded but search returned no results
- API rate limiting
- Incorrect API endpoint

**Solutions**:
1. Try switching between v2 and v4 in the CONFIG
2. Check the Västtrafik API status page
3. Verify your subscription includes location search endpoints

### Rate Limiting

If you encounter rate limiting:
1. Increase `time.sleep()` delay in the script
2. Reduce the number of search terms
3. Use the v2 `location.allstops` endpoint instead of searching

## API Endpoints Reference

### v2 API Endpoints
- `POST /token` - Get OAuth2 access token
- `GET /location.allstops` - Get all stops (recommended)
- `GET /location.name` - Search locations by text
- `GET /location.nearbystops` - Find stops near coordinates

### v4 API Endpoints
- `POST /token` - Get OAuth2 access token
- `GET /locations/by-text` - Search locations by text
- `GET /locations/by-coordinates` - Find locations near coordinates

## Examples

### Using v2 API (Get all stops at once)
```python
# In fetch_bus_stops_v2.py, set:
CONFIG = {
    "version": "v2",
    # ... other settings
}
```

### Using v4 API (Search-based)
```python
# In fetch_bus_stops_v2.py, set:
CONFIG = {
    "version": "v4",
    # ... other settings
}
```

### Custom Search Terms
Edit the `search_terms` list in the script:
```python
search_terms = ["göteborg", "mölndal", "partille", "lerum"]
```

## License

This project is provided as-is for educational and research purposes.

## Acknowledgments

- Västtrafik for providing the public API
- Swedish public transport data standards

## Links

- [Västtrafik Developer Portal](https://developer.vasttrafik.se)
- [API Documentation](https://developer.vasttrafik.se/portal)
- [Trafiklab](https://www.trafiklab.se/api/other-apis/vasttrafik/)
