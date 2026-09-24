# Boyfriend Location Display

A desk display that shows a live map of where my boyfriend is, sourced from
his iPhone via an iOS Shortcuts automation. Built on a Raspberry Pi 4B with
a DSI touchscreen, a WS2812B LED strip, and a speaker for status reactions.

This repo currently covers **Step 1: the location pipeline** — his phone
posts coordinates to a small server running on the Pi, which stores the
latest one for the display to poll.

## How it works

1. An iOS Shortcuts automation on his phone runs on a schedule (or on
   location change) and POSTs his current coordinates to the Pi.
2. A Flask server on the Pi (`server/app.py`) receives the POST, checks a
   shared secret, and saves the latest `{lat, lon, timestamp}` to disk.
3. Anything else on the Pi (the map renderer, the display loop) can `GET`
   the latest location from the same server.

## 1. Set up the server on the Pi

```bash
git clone https://github.com/kondovskii/boyfriend-location-display.git
cd boyfriend-location-display/server
pip3 install -r requirements.txt --break-system-packages
export LOCATION_SECRET="pick-something-long-and-random"
python3 app.py
```

The server listens on port `5050` on all interfaces.

## 2. Test it locally before touching his phone

From another terminal (or another machine on the same network):

```bash
# find the Pi's LAN IP first
hostname -I

# send a fake location
curl -X POST http://<pi-ip>:5050/location \
  -H "Content-Type: application/json" \
  -d '{"lat": 42.3149, "lon": -83.0364, "secret": "pick-something-long-and-random"}'

# read it back
curl http://<pi-ip>:5050/location
```

You should get back the same coordinates with a timestamp attached. Don't
move on to the Shortcuts step until this round-trip works.

## 3. Make the server reachable from outside your home network

His phone won't always be on your WiFi, so `http://<pi-ip>:5050` alone
only works while you're both on the same network. Pick one:

- **Tailscale (recommended)** — install it on the Pi and on his phone.
  Both devices join a private mesh network and get a stable address that
  works from anywhere, with no router configuration and no port left open
  to the public internet. This is the safest option since the shared
  secret is your only auth otherwise.
- **Port forwarding** — forward a port on your router to the Pi. Works,
  but exposes the Flask server directly to the internet; only reasonable
  with the shared-secret check in place and ideally HTTPS in front of it.
- **A tunnel (ngrok, Cloudflare Tunnel)** — quick to set up for testing,
  gives you a public URL without router changes, but free tiers often
  rotate the URL on restart.

Start with Tailscale if you want this to keep working without fiddling
with it later.

## 4. Set up the iOS Shortcuts automation (on his phone)

1. Open **Shortcuts** → **Automation** tab → **+** → **Create Personal
   Automation**.
2. Trigger: choose **Time of Day** (repeat every X minutes isn't natively
   supported, so most people use **"Time of Day"** repeated, or trigger
   off **"When I Arrive/Leave"** a location — for continuous tracking,
   a lightweight alternative is a **Time of Day** automation set to run
   every 15–30 minutes via the Shortcuts app's repeat option, or use the
   **"When Charger Connected/Disconnected"** trick some builds use — for a
   first version, start with a manual **Home Screen icon / widget** you
   both tap, then automate later once the pipeline works).
3. Add action: **Get Current Location**.
4. Add action: **Get Contents of URL**
   - URL: `http://<your-tailscale-or-public-address>:5050/location`
   - Method: `POST`
   - Headers: `Content-Type: application/json`
   - Request Body (JSON):
     ```json
     {
       "lat": "[Latitude from Get Current Location]",
       "lon": "[Longitude from Get Current Location]",
       "secret": "pick-something-long-and-random"
     }
     ```
5. Turn off **"Ask Before Running"** so it fires silently.

Test it by running the shortcut manually first (tap it in the Shortcuts
app) and confirming `curl http://<pi-ip>:5050/location` reflects his real
coordinates.

## Next steps

- Render the coordinates on a map image (`staticmap` or similar)
- Poll `/location` from a Tkinter fullscreen loop on the touchscreen
- Flag "stale" location (no update past a threshold) to drive the LED/
  speaker reactions
