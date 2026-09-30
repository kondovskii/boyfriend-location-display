#!/bin/bash
# Launches the whole pipeline: location server, map renderer, display, and
# the LED/speaker reactor, all in the background. Ctrl+C stops all of them.
#
# Run from the repo root:
#     export LOCATION_SECRET="pick-something-long-and-random"
#     ./scripts/run_all.sh

set -e

if [ -z "$LOCATION_SECRET" ]; then
    echo "LOCATION_SECRET is not set. Run: export LOCATION_SECRET=\"your-secret\""
    exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cleanup() {
    echo "Stopping all processes..."
    kill $(jobs -p) 2>/dev/null
}
trap cleanup EXIT

echo "Starting location server..."
(cd "$REPO_ROOT/server" && python3 app.py) &

sleep 2  # give the server a moment to come up before things start polling it

echo "Starting map renderer..."
(cd "$REPO_ROOT/display" && python3 render_map.py --loop --interval 60) &

echo "Starting display viewer..."
(cd "$REPO_ROOT/display" && python3 show_display.py) &

echo "Starting LED/speaker reactor..."
(cd "$REPO_ROOT/leds" && sudo -E python3 status_reactor.py) &

echo "All processes started. Press Ctrl+C to stop everything."
wait
