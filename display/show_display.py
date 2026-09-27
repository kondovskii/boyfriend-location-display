"""
Fullscreen viewer for the touchscreen. Watches map.png (written by
render_map.py) and reloads it whenever the file changes, so the display
stays in sync without the viewer and the renderer needing to talk to
each other directly.

Run render_map.py --loop in one terminal/process, and this in another:

    python3 show_display.py

Press Escape to quit (useful while testing on a desktop before deploying
to the Pi's touchscreen).
"""

import argparse
import os
import tkinter as tk

from PIL import Image, ImageTk

DEFAULT_IMAGE_PATH = "map.png"
DEFAULT_CHECK_INTERVAL_MS = 2000  # how often to check if the file changed


class MapViewer:
    def __init__(self, root: tk.Tk, image_path: str, check_interval_ms: int):
        self.root = root
        self.image_path = image_path
        self.check_interval_ms = check_interval_ms
        self.last_mtime = None
        self.photo_image = None  # keep a reference so Tkinter doesn't garbage-collect it

        self.label = tk.Label(root, bg="black")
        self.label.pack(fill=tk.BOTH, expand=True)

        root.bind("<Escape>", lambda event: root.destroy())

        self.load_image_if_changed()
        self.schedule_check()

    def load_image_if_changed(self) -> None:
        if not os.path.exists(self.image_path):
            return

        mtime = os.path.getmtime(self.image_path)
        if mtime == self.last_mtime:
            return  # file hasn't changed since we last loaded it

        self.last_mtime = mtime
        image = Image.open(self.image_path)
        self.photo_image = ImageTk.PhotoImage(image)
        self.label.configure(image=self.photo_image)

    def schedule_check(self) -> None:
        self.load_image_if_changed()
        self.root.after(self.check_interval_ms, self.schedule_check)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fullscreen viewer for the location map.")
    parser.add_argument("--image", default=DEFAULT_IMAGE_PATH,
                         help="Path to the map image to display")
    parser.add_argument("--interval", type=int, default=DEFAULT_CHECK_INTERVAL_MS,
                         help="Milliseconds between checks for an updated image")
    parser.add_argument("--windowed", action="store_true",
                         help="Run in a normal window instead of fullscreen (for testing on a desktop)")
    args = parser.parse_args()

    root = tk.Tk()
    root.title("Location Display")
    root.configure(bg="black")

    if not args.windowed:
        root.attributes("-fullscreen", True)

    MapViewer(root, args.image, args.interval)
    root.mainloop()


if __name__ == "__main__":
    main()
