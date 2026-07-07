"""
config.py
=========
Central configuration for GestureCanvas (Desktop Edition).

Every tunable constant used across the app lives here so behaviour can be
changed in one place without hunting through the codebase. Nothing here
reads from environment variables on purpose -- this is a local desktop
tool meant to run instantly with `python main.py`, so there is no
deployment-specific configuration to manage.
"""

# --------------------------------------------------------------------------
# Window / camera
# --------------------------------------------------------------------------
WINDOW_NAME = "GestureCanvas"
CAMERA_INDEX = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
FLIP_CAMERA = True          # mirror the feed so movement feels natural

# --------------------------------------------------------------------------
# MediaPipe Hands
# --------------------------------------------------------------------------
MAX_NUM_HANDS = 1
DETECTION_CONFIDENCE = 0.7
TRACKING_CONFIDENCE = 0.6

# --------------------------------------------------------------------------
# Drawing / brush
# --------------------------------------------------------------------------
DEFAULT_BRUSH_THICKNESS = 6
MIN_BRUSH_THICKNESS = 2
MAX_BRUSH_THICKNESS = 40

DEFAULT_GLOW_INTENSITY = 5      # 0 - 10, controls bloom blur size/strength
MIN_GLOW_INTENSITY = 0
MAX_GLOW_INTENSITY = 10

CANVAS_BACKGROUND = (12, 12, 18)   # near-black BGR, ideal backdrop for neon strokes
MAX_UNDO_STATES = 25

# Smoothing factor for cursor interpolation (0 = no smoothing, 1 = frozen).
CURSOR_SMOOTHING = 0.35
# Maximum pixel gap between two consecutive tracked points before we
# interpolate extra points in between (keeps fast strokes gap-free).
MAX_POINT_GAP = 6

# --------------------------------------------------------------------------
# Neon color palette (BGR tuples) -- selectable with number keys 1-8
# --------------------------------------------------------------------------
COLOR_PALETTE = [
    ("Neon Cyan",    (255, 220, 40)),
    ("Neon Magenta", (230, 60, 255)),
    ("Neon Green",   (80, 255, 120)),
    ("Neon Yellow",  (40, 235, 255)),
    ("Neon Orange",  (30, 130, 255)),
    ("Electric Blue", (255, 120, 40)),
    ("Hot Pink",     (150, 60, 255)),
    ("Pure White",   (255, 255, 255)),
]

# --------------------------------------------------------------------------
# Particle system
# --------------------------------------------------------------------------
PARTICLES_PER_DRAW_EVENT = 3
PARTICLE_MIN_LIFETIME = 18     # frames
PARTICLE_MAX_LIFETIME = 38
PARTICLE_MIN_SPEED = 0.6
PARTICLE_MAX_SPEED = 2.2
PARTICLE_MAX_COUNT = 400        # hard cap to keep frame time bounded
AMBIENT_PARTICLE_SPAWN_CHANCE = 0.35  # per-frame chance to spawn a free-floating ambient particle

# --------------------------------------------------------------------------
# Storage
# --------------------------------------------------------------------------
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(BASE_DIR, "screenshots")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# --------------------------------------------------------------------------
# OCR
# --------------------------------------------------------------------------
TESSERACT_CMD = ""   # leave blank to use system PATH; set explicit path on Windows if needed

# --------------------------------------------------------------------------
# Voice commands
# --------------------------------------------------------------------------
VOICE_LISTEN_TIMEOUT = 4          # seconds to wait for a phrase to start
VOICE_PHRASE_TIME_LIMIT = 4       # max seconds for a single phrase
VOICE_ENERGY_THRESHOLD = 300      # ambient noise energy threshold for SpeechRecognition

# --------------------------------------------------------------------------
# UI / HUD
# --------------------------------------------------------------------------
FONT = "FONT_HERSHEY_DUPLEX"       # resolved to cv2 constant in ui.py
HUD_ACCENT = (255, 220, 40)        # cyan-ish accent used for borders/highlights
HUD_TEXT_COLOR = (235, 235, 245)
HUD_MUTED_TEXT = (150, 150, 165)
HUD_PANEL_ALPHA = 0.55             # translucency of glass-style HUD panels
TOAST_LIFETIME_SECONDS = 2.5
