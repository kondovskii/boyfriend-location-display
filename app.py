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


if __name__ == "__main__":
    # 0.0.0.0 so it's reachable from other devices on the network, not just localhost
    app.run(host="0.0.0.0", port=5050)
