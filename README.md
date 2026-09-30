# Boyfriend Location Display

A desk display that shows a live map of where my boyfriend is, sourced from
his iPhone via an iOS Shortcuts automation. Built on a Raspberry Pi 4B with
a DSI touchscreen, a WS2812B LED strip, and a speaker for status reactions.

## How it works

1. An iOS Shortcuts automation on his phone runs on a schedule and POSTs
   his current coordinates to the Pi.
2. A Flask server on the Pi (`server/app.py`) receives the POST, checks a
   shared secret, and saves the latest `{lat, lon, timestamp}` to disk. It
   also exposes a `/status` endpoint that classifies the location as
   `live`, `stale`, or `offline` based on how long ago it was updated.
3. `display/render_map.py` polls the server and draws a map image with a
   marker at his location.
4. `display/show_display.py` shows that map fullscreen on the touchscreen
   and reloads it whenever it changes.
5. `leds/status_reactor.py` polls `/status` and drives the LED strip +
   speaker: green when live, amber when stale, red plus an alert tone the
   moment it goes offline.
6. `scripts/run_all.sh` starts all of the above together with one command.

## Repo layout

```
server/     Flask server: receives locations, serves /location and /status
display/    Map rendering + fullscreen touchscreen viewer
leds/       WS2812B + speaker reactions to location status
scripts/    Convenience script to launch everything at once
```

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

# check the derived status
curl http://<pi-ip>:5050/status
```

You should get back the same coordinates with a timestamp attached, and
`/status` should say `"status": "live"`. Don't move on to the Shortcuts
step until this round-trip works.

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
2. Trigger: **Time of Day**, repeating every 15–30 minutes. For a first
   version, a manual Home Screen shortcut you both tap works too —
   automate it once the pipeline is confirmed working.
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

Test it by running the shortcut manually first, then confirming
`curl http://<pi-ip>:5050/location` reflects his real coordinates.

## 5. Render and display the map

```bash
cd display
pip3 install -r requirements.txt --break-system-packages
python3 render_map.py --loop --interval 60   # keeps redrawing map.png
python3 show_display.py                       # shows it fullscreen, auto-reloads
```

Use `python3 show_display.py --windowed` to preview in a normal window
before deploying to the touchscreen.

## 6. Wire up the LED strip and speaker reactions

```bash
cd leds
pip3 install -r requirements.txt --break-system-packages
sudo python3 status_reactor.py
```

Requires the WS2812B strip on GPIO18 and the MAX98357A amp set up as the
default ALSA output (I2S overlay enabled in `/boot/config.txt`). Adjust
`LED_COUNT` in `status_reactor.py` to match your actual strip length.

## 7. Run everything at once

```bash
export LOCATION_SECRET="pick-something-long-and-random"
chmod +x scripts/run_all.sh   # first time only
./scripts/run_all.sh
```

Starts the server, renderer, display, and LED/speaker reactor together;
`Ctrl+C` stops all of them.

## Next steps

- Enclosure / final assembly
- Content video
