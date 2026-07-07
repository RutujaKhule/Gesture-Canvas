"""
utils.py
========
Small, dependency-free helper utilities shared across the app: FPS
measurement, point interpolation for smooth strokes, safe filenames, and a
lightweight on-screen toast/notification queue.
"""

import math
import time
import os

import config


class FPSCounter:
    """Rolling FPS counter based on a short moving window of frame timestamps."""

    def __init__(self, window_size: int = 20):
        self.window_size = window_size
        self._timestamps = []

    def tick(self) -> float:
        """Call once per frame. Returns the current smoothed FPS value."""
        now = time.time()
        self._timestamps.append(now)
        if len(self._timestamps) > self.window_size:
            self._timestamps.pop(0)
        if len(self._timestamps) < 2:
            return 0.0
        elapsed = self._timestamps[-1] - self._timestamps[0]
        if elapsed <= 0:
            return 0.0
        return (len(self._timestamps) - 1) / elapsed


def distance(p1, p2) -> float:
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def interpolate_points(p1, p2, max_gap: int = config.MAX_POINT_GAP):
    """
    Return a list of points between p1 and p2 (inclusive of p2) spaced no
    further apart than `max_gap` pixels. This keeps fast hand movements
    from leaving visible gaps in the drawn stroke ("smooth drawing
    interpolation").
    """
    d = distance(p1, p2)
    if d <= max_gap:
        return [p2]
    steps = int(d // max_gap) + 1
    points = []
    for i in range(1, steps + 1):
        t = i / steps
        x = int(p1[0] + (p2[0] - p1[0]) * t)
        y = int(p1[1] + (p2[1] - p1[1]) * t)
        points.append((x, y))
    return points


def exponential_smooth(prev_point, new_point, alpha: float):
    """Blend `new_point` toward `prev_point` for jitter-free cursor tracking."""
    if prev_point is None:
        return new_point
    x = alpha * new_point[0] + (1 - alpha) * prev_point[0]
    y = alpha * new_point[1] + (1 - alpha) * prev_point[1]
    return (int(x), int(y))


def timestamped_filename(prefix: str, ext: str) -> str:
    stamp = time.strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{stamp}.{ext}"


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


class ToastQueue:
    """
    Tiny in-memory queue of short-lived status messages ("Canvas cleared",
    "Saved as PNG", ...) rendered as HUD toasts by ui.py.
    """

    def __init__(self, lifetime_seconds: float = config.TOAST_LIFETIME_SECONDS):
        self.lifetime_seconds = lifetime_seconds
        self._messages = []  # list of (text, expires_at)

    def push(self, text: str):
        expires_at = time.time() + self.lifetime_seconds
        self._messages.append([text, expires_at])

    def active(self):
        now = time.time()
        self._messages = [m for m in self._messages if m[1] > now]
        return [m[0] for m in self._messages]
