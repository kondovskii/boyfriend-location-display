"""
Minimal location-tracking server.

POST /location  -> receives {"lat": ..., "lon": ..., "secret": ...} from
                    the iOS Shortcuts automation, stores it with a timestamp
GET  /location   -> returns the most recently stored location
"""

from flask import Flask, request, jsonify
import json
import os
from datetime import datetime, timezone

app = Flask(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), "latest_location.json")

# Set a real secret before deploying: export LOCATION_SECRET="something-long-and-random"
SHARED_SECRET = os.environ.get("LOCATION_SECRET", "change-me")

# How old a location can be before we consider it stale / offline
STALE_AFTER_SECONDS = int(os.environ.get("STALE_AFTER_SECONDS", 600))     # 10 min
OFFLINE_AFTER_SECONDS = int(os.environ.get("OFFLINE_AFTER_SECONDS", 1800))  # 30 min


def classify_status(timestamp_str: str) -> tuple[str, float]:
    """Returns (status, seconds_since_update) for a stored ISO timestamp."""
    last_update = datetime.fromisoformat(timestamp_str)
    seconds_elapsed = (datetime.now(timezone.utc) - last_update).total_seconds()

    if seconds_elapsed <= STALE_AFTER_SECONDS:
        status = "live"
    elif seconds_elapsed <= OFFLINE_AFTER_SECONDS:
        status = "stale"
    else:
        status = "offline"

    return status, seconds_elapsed



@app.route("/location", methods=["POST"])
def update_location():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "invalid or missing JSON body"}), 400

    if data.get("secret") != SHARED_SECRET:
        return jsonify({"error": "unauthorized"}), 401

    lat = data.get("lat")
    lon = data.get("lon")
    if lat is None or lon is None:
        return jsonify({"error": "lat and lon are required"}), 400

    payload = {
        "lat": lat,
        "lon": lon,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    with open(DATA_FILE, "w") as f:
        json.dump(payload, f)

    return jsonify({"status": "ok"}), 200


@app.route("/location", methods=["GET"])
def get_location():
    if not os.path.exists(DATA_FILE):
        return jsonify({"error": "no location received yet"}), 404

    with open(DATA_FILE) as f:
        return jsonify(json.load(f)), 200
@app.route("/status", methods=["GET"])
def get_status():
    if not os.path.exists(DATA_FILE):
        return jsonify({"status": "offline", "reason": "no location received yet"}), 200

    with open(DATA_FILE) as f:
        location = json.load(f)

    status, seconds_elapsed = classify_status(location["timestamp"])

    return jsonify({
        "status": status,
        "seconds_since_update": round(seconds_elapsed),
        "lat": location["lat"],
        "lon": location["lon"],
        "timestamp": location["timestamp"],
    }), 200

if __name__ == "__main__":
    # 0.0.0.0 so it's reachable from other devices on the network, not just localhost
    app.run(host="0.0.0.0", port=5050)
