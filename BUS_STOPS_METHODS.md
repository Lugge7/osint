# Bus Stop Fetching Methods for Västra Götalands län

This document compares different methods for downloading all bus stops in Västra Götalands län, Sweden.

## Available Methods

### 1. **Trafiklab GTFS Sweden 3** 🌟 RECOMMENDED

**File:** `fetch_bus_stops_gtfs.py`

**Pros:**
- ✅ Single download gets ALL stops in Sweden (including Västra Götaland)
- ✅ Official, high-quality data from national platform
- ✅ Standard GTFS format (widely used and documented)
- ✅ Updated daily (05:00-06:00)
- ✅ Free with API key (Bronze tier sufficient)
- ✅ No pagination/searching needed
- ✅ Complete and accurate

**Cons:**
- ⚠️ Requires free API key registration
- ⚠️ Large download (~100-200 MB ZIP file)
- ⚠️ Rate limited (Bronze: 50 calls/month is usually enough)

**Best for:** Official, complete, and accurate data

**Setup:**
1. Register at https://www.trafiklab.se/
2. Create a project
3. Subscribe to "GTFS Sweden 3" API (Bronze tier is free)
4. Copy API key and set in script

**Usage:**
```bash
python3 fetch_bus_stops_gtfs.py
```

---

### 2. **OpenStreetMap Overpass API** 🆓 NO API KEY

**File:** `fetch_bus_stops_osm.py`

**Pros:**
- ✅ No API key required
- ✅ Free and open data
- ✅ Global coverage
- ✅ Community-maintained
- ✅ Additional metadata (wheelchair access, shelter, bench, etc.)

**Cons:**
- ⚠️ Data quality varies by region
- ⚠️ May not be as complete as official sources
- ⚠️ Depends on community contributions
- ⚠️ Query can be slow for large regions
- ⚠️ Some stops may be missing or outdated

**Best for:** Quick testing, no API key needed, or when you need accessibility info

**Usage:**
```bash
python3 fetch_bus_stops_osm.py
```

No setup required - just run it!

---

### 3. **Västtrafik API Direct** (Original Methods)

**Files:** `fetch_bus_stops.py`, `fetch_bus_stops_v2.py`

**Pros:**
- ✅ Direct from source (Västtrafik)
- ✅ Real-time API access
- ✅ Detailed stop information

**Cons:**
- ⚠️ Requires many API calls (rate limiting issues)
- ⚠️ Slow (must search with many queries)
- ⚠️ May miss stops due to search limitations
- ⚠️ Requires API key
- ⚠️ More complex implementation

**Best for:** Real-time queries, specific stop lookups

---

## Comparison Table

| Method | API Key? | Completeness | Speed | Data Quality | Setup Complexity |
|--------|----------|--------------|-------|--------------|------------------|
| **Trafiklab GTFS** | Yes (free) | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐⭐ Fast (single download) | ⭐⭐⭐⭐⭐ Official | ⭐⭐ Easy |
| **OpenStreetMap** | No | ⭐⭐⭐ Good | ⭐⭐⭐ Medium | ⭐⭐⭐⭐ Community | ⭐ Very Easy |
| **Västtrafik API** | Yes | ⭐⭐⭐ Good | ⭐⭐ Slow | ⭐⭐⭐⭐⭐ Official | ⭐⭐⭐ Medium |

---

## Recommendations

### For Production Use:
**Use Trafiklab GTFS** - Most reliable, complete, and officially maintained.

### For Quick Testing/Prototyping:
**Use OpenStreetMap** - No API key needed, fast to set up.

### For Real-time Applications:
**Use Västtrafik API** - If you need real-time departures and arrivals.

---

## Data Formats

### GTFS Format (Trafiklab)
Standard transit feed format with files:
- `stops.txt` - All stops with coordinates
- `routes.txt` - Route information
- `trips.txt` - Trip schedules
- `agency.txt` - Transit agencies

### OSM Format (OpenStreetMap)
JSON with detailed tags:
- Name, coordinates
- Operator, network
- Accessibility (wheelchair, tactile_paving)
- Amenities (shelter, bench)

### Västtrafik API Format
JSON with API-specific structure:
- GID (Global ID)
- Name, coordinates
- Municipality
- Location type

---

## Example Outputs

All scripts save data to JSON files:

**GTFS output:** `bus_stops_gtfs.json`
**OSM output:** `bus_stops_osm.json`
**Västtrafik output:** `bus_stops.json`

Example JSON structure:
```json
{
  "total_stops": 5234,
  "source": "Trafiklab GTFS Sweden 3",
  "stops": [
    {
      "stop_id": "740000001",
      "stop_name": "Centralstationen",
      "latitude": 57.708870,
      "longitude": 11.973479
    }
  ]
}
```

---

## License Information

- **Trafiklab GTFS:** CC0 1.0 Universal (Public Domain)
- **OpenStreetMap:** ODbL (Open Database License)
- **Västtrafik API:** Check Västtrafik's terms of service

---

## Troubleshooting

### Trafiklab Issues:
- **404 Error:** Check API key, ensure you're subscribed to GTFS Sweden 3
- **Rate limit:** Bronze tier allows 50 downloads/month
- **Slow download:** File is ~100-200 MB, may take 2-5 minutes

### OSM Issues:
- **Timeout:** Reduce bounding box area
- **Missing stops:** Data depends on community mapping
- **Slow query:** Use a different Overpass instance

### Västtrafik Issues:
- **Auth failed:** Check API credentials
- **Rate limited:** Too many requests, add delays
- **Missing stops:** Search strategy may not cover all areas

---

## Further Reading

- [Trafiklab Documentation](https://www.trafiklab.se/api/)
- [GTFS Specification](https://gtfs.org/)
- [OpenStreetMap Public Transport](https://wiki.openstreetmap.org/wiki/Public_transport)
- [Västtrafik Developer Portal](https://developer.vasttrafik.se/)
