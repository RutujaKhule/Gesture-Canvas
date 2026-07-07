"""
drawing.py
==========
The persistent drawing canvas: stroke rendering, neon glow/bloom
compositing, brush thickness, undo history, clearing, saving, and an
OCR-friendly export.

Strokes are rendered onto a black "ink" layer at full brightness. Each
frame, `composite()` builds the glowing look by blurring a copy of that
layer (bloom) and additively blending it on top of the live camera frame,
which is what gives GestureCanvas its neon look.
"""

import cv2
import numpy as np

import config
from utils import interpolate_points, exponential_smooth, timestamped_filename, ensure_dir


class Canvas:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

        # The persistent ink layer -- what actually gets undone/saved/OCR'd.
        self.strokes = np.zeros((height, width, 3), dtype=np.uint8)

        self.color = config.COLOR_PALETTE[0][1]
        self.color_name = config.COLOR_PALETTE[0][0]
        self.thickness = config.DEFAULT_BRUSH_THICKNESS
        self.glow_intensity = config.DEFAULT_GLOW_INTENSITY

        self._undo_stack = []
        self._smoothed_point = None
        self._last_drawn_point = None
        self._stroke_pre_snapshot = None
        self._is_drawing = False

    # ------------------------------------------------------------------ #
    # Tool state
    # ------------------------------------------------------------------ #
    def set_color(self, bgr, name: str = ""):
        self.color = bgr
        if name:
            self.color_name = name

    def set_color_index(self, index: int):
        index = index % len(config.COLOR_PALETTE)
        name, bgr = config.COLOR_PALETTE[index]
        self.color, self.color_name = bgr, name

    def set_thickness(self, value: int):
        self.thickness = int(np.clip(value, config.MIN_BRUSH_THICKNESS, config.MAX_BRUSH_THICKNESS))

    def change_thickness(self, delta: int):
        self.set_thickness(self.thickness + delta)

    def set_glow_intensity(self, value: int):
        self.glow_intensity = int(np.clip(value, config.MIN_GLOW_INTENSITY, config.MAX_GLOW_INTENSITY))

    def change_glow_intensity(self, delta: int):
        self.set_glow_intensity(self.glow_intensity + delta)

    # ------------------------------------------------------------------ #
    # Stroke lifecycle
    # ------------------------------------------------------------------ #
    def begin_stroke(self, raw_point):
        """Call the first frame a DRAW gesture becomes active."""
        self._stroke_pre_snapshot = self.strokes.copy()
        self._smoothed_point = raw_point
        self._last_drawn_point = raw_point
        self._is_drawing = True
        # A tiny dot so a single-frame tap still leaves a visible mark.
        cv2.circle(self.strokes, raw_point, max(1, self.thickness // 2), self.color, -1, lineType=cv2.LINE_AA)

    def extend_stroke(self, raw_point):
        """Call on every subsequent frame the DRAW gesture stays active."""
        smoothed = exponential_smooth(self._smoothed_point, raw_point, config.CURSOR_SMOOTHING)
        self._smoothed_point = smoothed

        points_to_draw = interpolate_points(self._last_drawn_point, smoothed)
        for pt in points_to_draw:
            cv2.line(self.strokes, self._last_drawn_point, pt, self.color, self.thickness, lineType=cv2.LINE_AA)
            self._last_drawn_point = pt
        return smoothed

    def end_stroke(self):
        """Call the frame a DRAW gesture ends (fist / hand lost). Commits undo history."""
        if self._is_drawing and self._stroke_pre_snapshot is not None:
            self._undo_stack.append(self._stroke_pre_snapshot)
            if len(self._undo_stack) > config.MAX_UNDO_STATES:
                self._undo_stack.pop(0)
        self._is_drawing = False
        self._smoothed_point = None
        self._last_drawn_point = None
        self._stroke_pre_snapshot = None

    @property
    def is_drawing(self):
        return self._is_drawing

    # ------------------------------------------------------------------ #
    # History / clearing
    # ------------------------------------------------------------------ #
    def undo(self) -> bool:
        if not self._undo_stack:
            return False
        self.strokes = self._undo_stack.pop()
        return True

    def clear(self):
        self._undo_stack.append(self.strokes.copy())
        if len(self._undo_stack) > config.MAX_UNDO_STATES:
            self._undo_stack.pop(0)
        self.strokes = np.zeros((self.height, self.width, 3), dtype=np.uint8)

    # ------------------------------------------------------------------ #
    # Rendering
    # ------------------------------------------------------------------ #
    def composite(self, camera_frame_bgr):
        """
        Build the final displayed frame: live camera feed with the neon
        ink layer bloomed and additively blended on top.
        """
        if self.glow_intensity <= 0:
            glow = self.strokes
        else:
            # Blur radius and blend weight both scale with glow_intensity (0-10).
            ksize = 1 + 2 * self.glow_intensity  # odd kernel size: 1,3,5...21
            blurred = cv2.GaussianBlur(self.strokes, (ksize, ksize), 0)
            weight = 0.35 + 0.09 * self.glow_intensity  # up to ~1.25
            glow = cv2.addWeighted(self.strokes, 1.0, blurred, weight, 0)

        return cv2.add(camera_frame_bgr, glow)

    def get_raw(self):
        return self.strokes.copy()

    def has_ink(self) -> bool:
        return cv2.countNonZero(cv2.cvtColor(self.strokes, cv2.COLOR_BGR2GRAY)) > 0

    def export_for_ocr(self):
        """
        Return a white-background / black-ink image of the current drawing,
        which Tesseract reads far more reliably than neon-on-black.
        """
        gray = cv2.cvtColor(self.strokes, cv2.COLOR_BGR2GRAY)
        _, ink_mask = cv2.threshold(gray, 15, 255, cv2.THRESH_BINARY)
        ocr_image = np.full((self.height, self.width), 255, dtype=np.uint8)
        ocr_image[ink_mask > 0] = 0
        # Thicken slightly so thin neon strokes read as solid handwriting strokes.
        kernel = np.ones((3, 3), np.uint8)
        ocr_image = cv2.erode(ocr_image, kernel, iterations=1)
        return ocr_image

    # ------------------------------------------------------------------ #
    # Saving
    # ------------------------------------------------------------------ #
    def save(self, composite_frame_bgr=None, prefix: str = "gesturecanvas"):
        """
        Save the current artwork to disk (PNG). Saves the glowing composite
        if provided, otherwise falls back to the raw ink layer on black.
        Returns the absolute file path.
        """
        ensure_dir(config.SAVE_DIR)
        image = composite_frame_bgr if composite_frame_bgr is not None else self.strokes
        filename = timestamped_filename(prefix, "png")
        path = f"{config.SAVE_DIR}/{filename}"
        cv2.imwrite(path, image)
        return path
