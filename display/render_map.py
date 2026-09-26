"""
Fetches the latest location from the Flask server and renders it as a map
image with a marker, ready to be shown on the touchscreen.

Run once:
    python3 render_map.py

Run continuously, redrawing on an interval:
    python3 render_map.py --loop --interval 60
"""

import argparse
import sys
import time

import requests
from staticmap import StaticMap, CircleMarker

DEFAULT_SERVER_URL = "http://127.0.0.1:5050/location"
DEFAULT_OUTPUT_PATH = "map.png"
DEFAULT_ZOOM = 14
MAP_WIDTH = 800
MAP_HEIGHT = 480  # matches the official 7" touchscreen resolution


def fetch_location(server_url: str) -> dict:
    """GET the latest {lat, lon, timestamp} from the location server."""
    response = requests.get(server_url, timeout=5)
    response.raise_for_status()
    return response.json()


def render_map(lat: float, lon: float, output_path: str, zoom: int = DEFAULT_ZOOM) -> None:
    """Draw a map centered on (lat, lon) with a marker, save it to output_path."""
    map_image = StaticMap(MAP_WIDTH, MAP_HEIGHT)
    marker = CircleMarker((lon, lat), "#FF3B30", 18)  # staticmap wants (lon, lat)
    map_image.add_marker(marker)

    rendered = map_image.render(zoom=zoom)
    rendered.save(output_path)


def run_once(server_url: str, output_path: str) -> None:
    location = fetch_location(server_url)
    render_map(location["lat"], location["lon"], output_path)
    print(f"Rendered {output_path} for lat={location['lat']}, lon={location['lon']}, "
          f"as of {location['timestamp']}")


def run_loop(server_url: str, output_path: str, interval: int) -> None:
    while True:
        try:
            run_once(server_url, output_path)
        except requests.RequestException as exc:
            print(f"Couldn't fetch location: {exc}", file=sys.stderr)
        time.sleep(interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render the latest location as a map image.")
    parser.add_argument("--server", default=DEFAULT_SERVER_URL,
                         help="URL of the location server's GET endpoint")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_PATH,
                         help="Where to save the rendered map image")
    parser.add_argument("--zoom", type=int, default=DEFAULT_ZOOM,
                         help="Map zoom level (higher = more zoomed in)")
    parser.add_argument("--loop", action="store_true",
                         help="Keep re-fetching and re-rendering on an interval")
    parser.add_argument("--interval", type=int, default=60,
                         help="Seconds between redraws when --loop is set")
    args = parser.parse_args()

    if args.loop:
        run_loop(args.server, args.output, args.interval)
    else:
        run_once(args.server, args.output)
