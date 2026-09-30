"""
Polls the location server's /status endpoint and reacts with the WS2812B
LED strip and the speaker:

    live    -> steady green
    stale   -> steady amber
    offline -> steady red, plus a two-tone alert sound the moment it
               *becomes* offline (not on every poll)

Needs root to drive the LED strip's PWM output:

    sudo python3 status_reactor.py
"""

import argparse
import time

import numpy as np
import requests
import sounddevice as sd
from rpi_ws281x import PixelStrip, Color

DEFAULT_SERVER_URL = "http://127.0.0.1:5050/status"
DEFAULT_POLL_INTERVAL = 15  # seconds

# --- LED strip config: adjust these to match your actual strip/wiring ---
LED_COUNT = 30          # how many pixels are on the strip you're using
LED_PIN = 18            # GPIO18 (PWM0) is the standard data pin for WS2812B on a Pi
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 150    # 0-255
LED_INVERT = False
LED_CHANNEL = 0

COLOR_LIVE = Color(0, 200, 0)       # green
COLOR_STALE = Color(230, 160, 0)    # amber
COLOR_OFFLINE = Color(220, 0, 0)    # red

SAMPLE_RATE = 44100


def set_strip_color(strip: PixelStrip, color) -> None:
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
    strip.show()


def play_tone(frequency: float, duration: float) -> None:
    """Synthesizes and plays a plain sine-wave beep, no audio file needed."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    tone = np.sin(frequency * t * 2 * np.pi)
    audio = (tone * 0.3 * 32767).astype(np.int16)
    sd.play(audio, SAMPLE_RATE)
    sd.wait()


def play_offline_alert() -> None:
    play_tone(880, 0.15)
    time.sleep(0.05)
    play_tone(660, 0.25)


def fetch_status(server_url: str) -> dict:
    response = requests.get(server_url, timeout=5)
    response.raise_for_status()
    return response.json()


def run(server_url: str, poll_interval: int) -> None:
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()

    last_status = None

    while True:
        try:
            data = fetch_status(server_url)
            status = data["status"]

            if status == "live":
                set_strip_color(strip, COLOR_LIVE)
            elif status == "stale":
                set_strip_color(strip, COLOR_STALE)
            else:  # offline
                set_strip_color(strip, COLOR_OFFLINE)
                if last_status != "offline":
                    play_offline_alert()  # only alert on the transition, not every poll

            last_status = status

        except requests.RequestException as exc:
            print(f"Couldn't fetch status: {exc}")

        time.sleep(poll_interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="React to location status with LEDs and sound.")
    parser.add_argument("--server", default=DEFAULT_SERVER_URL)
    parser.add_argument("--interval", type=int, default=DEFAULT_POLL_INTERVAL)
    args = parser.parse_args()

    run(args.server, args.interval)
