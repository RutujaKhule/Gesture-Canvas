"""
ui.py
=====
All on-screen HUD rendering for GestureCanvas: translucent "glass" status
panels, the color palette strip, status badges, FPS readout, toast
notifications, the keyboard-shortcut help overlay, and the native OpenCV
trackbar control window used for the brush-thickness and glow-intensity
sliders.
"""

import cv2

import config

FONT = cv2.FONT_HERSHEY_DUPLEX
FONT_SMALL = cv2.FONT_HERSHEY_SIMPLEX

CONTROLS_WINDOW = "GestureCanvas Controls"


# ---------------------------------------------------------------------- #
# Native trackbar control window (brush thickness / glow intensity sliders)
# ---------------------------------------------------------------------- #
def create_control_window():
    cv2.namedWindow(CONTROLS_WINDOW, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(CONTROLS_WINDOW, 420, 120)
    cv2.createTrackbar("Brush Thickness", CONTROLS_WINDOW, config.DEFAULT_BRUSH_THICKNESS,
                        config.MAX_BRUSH_THICKNESS, lambda _v: None)
    cv2.setTrackbarMin("Brush Thickness", CONTROLS_WINDOW, config.MIN_BRUSH_THICKNESS)
    cv2.createTrackbar("Glow Intensity", CONTROLS_WINDOW, config.DEFAULT_GLOW_INTENSITY,
                        config.MAX_GLOW_INTENSITY, lambda _v: None)


def read_trackbars():
    """Returns (brush_thickness, glow_intensity) from the control window."""
    thickness = cv2.getTrackbarPos("Brush Thickness", CONTROLS_WINDOW)
    glow = cv2.getTrackbarPos("Glow Intensity", CONTROLS_WINDOW)
    return thickness, glow


def sync_trackbars(thickness: int, glow: int):
    """Push programmatic changes (e.g. keyboard +/-) back onto the sliders."""
    cv2.setTrackbarPos("Brush Thickness", CONTROLS_WINDOW, thickness)
    cv2.setTrackbarPos("Glow Intensity", CONTROLS_WINDOW, glow)


# ---------------------------------------------------------------------- #
# Glass-style translucent panel helper
# ---------------------------------------------------------------------- #
def glass_panel(frame, x, y, w, h, alpha=config.HUD_PANEL_ALPHA, border_color=config.HUD_ACCENT):
    """Alpha-blend a translucent dark panel with a subtle accent border, in place."""
    x2, y2 = x + w, y + h
    overlay = frame.copy()
    cv2.rectangle(overlay, (x, y), (x2, y2), (18, 18, 26), -1)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, dst=frame)
    cv2.rectangle(frame, (x, y), (x2, y2), border_color, 1, lineType=cv2.LINE_AA)


# ---------------------------------------------------------------------- #
# Status HUD (top-left): FPS, gesture badge, hand-detection dot
# ---------------------------------------------------------------------- #
def draw_status_hud(frame, fps: float, gesture: str, hand_detected: bool):
    panel_w, panel_h = 260, 88
    glass_panel(frame, 16, 16, panel_w, panel_h)

    dot_color = (90, 230, 110) if hand_detected else (90, 90, 100)
    cv2.circle(frame, (34, 40), 6, dot_color, -1, lineType=cv2.LINE_AA)
    cv2.putText(frame, "Hand Tracking", (50, 45), FONT_SMALL, 0.55, config.HUD_TEXT_COLOR, 1, cv2.LINE_AA)

    badge_color = (90, 230, 110) if gesture == "DRAW" else (90, 130, 235) if gesture == "STOP" else (120, 120, 130)
    badge_text = {"DRAW": "DRAWING", "STOP": "STOPPED", "NO_HAND": "NO HAND"}.get(gesture, gesture)
    cv2.rectangle(frame, (28, 56), (28 + 110, 82), badge_color, -1, lineType=cv2.LINE_AA)
    cv2.putText(frame, badge_text, (36, 74), FONT_SMALL, 0.55, (15, 15, 20), 2, cv2.LINE_AA)

    cv2.putText(frame, f"{fps:4.1f} FPS", (150, 74), FONT, 0.6, config.HUD_ACCENT, 1, cv2.LINE_AA)


# ---------------------------------------------------------------------- #
# Tool panel (top-right): color, brush thickness, glow intensity
# ---------------------------------------------------------------------- #
def draw_tool_hud(frame, color_name, color_bgr, thickness, glow_intensity):
    w = frame.shape[1]
    panel_w, panel_h = 250, 88
    x = w - panel_w - 16
    glass_panel(frame, x, 16, panel_w, panel_h)

    cv2.circle(frame, (x + 20, 40), 10, color_bgr, -1, lineType=cv2.LINE_AA)
    cv2.circle(frame, (x + 20, 40), 10, (255, 255, 255), 1, lineType=cv2.LINE_AA)
    cv2.putText(frame, color_name, (x + 40, 46), FONT_SMALL, 0.55, config.HUD_TEXT_COLOR, 1, cv2.LINE_AA)

    cv2.putText(frame, f"Brush: {thickness}px", (x + 16, 68), FONT_SMALL, 0.5, config.HUD_MUTED_TEXT, 1, cv2.LINE_AA)
    cv2.putText(frame, f"Glow: {glow_intensity}/10", (x + 130, 68), FONT_SMALL, 0.5, config.HUD_MUTED_TEXT, 1, cv2.LINE_AA)


# ---------------------------------------------------------------------- #
# Color palette strip (bottom): number keys 1-8 select a color
# ---------------------------------------------------------------------- #
def draw_palette(frame, active_index: int):
    h, w = frame.shape[:2]
    swatch_size = 34
    gap = 10
    count = len(config.COLOR_PALETTE)
    total_w = count * swatch_size + (count - 1) * gap
    start_x = (w - total_w) // 2
    y = h - swatch_size - 20

    glass_panel(frame, start_x - 14, y - 10, total_w + 28, swatch_size + 20, alpha=0.45)

    for i, (name, bgr) in enumerate(config.COLOR_PALETTE):
        cx = start_x + i * (swatch_size + gap)
        cv2.rectangle(frame, (cx, y), (cx + swatch_size, y + swatch_size), bgr, -1, lineType=cv2.LINE_AA)
        border_color = (255, 255, 255) if i == active_index else (90, 90, 100)
        border_thickness = 2 if i == active_index else 1
        cv2.rectangle(frame, (cx, y), (cx + swatch_size, y + swatch_size), border_color, border_thickness, cv2.LINE_AA)
        cv2.putText(frame, str(i + 1), (cx + 11, y + swatch_size + 16), FONT_SMALL, 0.42,
                    config.HUD_MUTED_TEXT, 1, cv2.LINE_AA)


# ---------------------------------------------------------------------- #
# Voice status indicator
# ---------------------------------------------------------------------- #
def draw_voice_indicator(frame, listening: bool, available: bool):
    h = frame.shape[0]
    x, y = 16, h - 128
    if not available:
        text, color = "Voice: unavailable", config.HUD_MUTED_TEXT
    elif listening:
        text, color = "Voice: listening...", (90, 230, 110)
    else:
        text, color = "Voice: off (press V)", config.HUD_MUTED_TEXT
    glass_panel(frame, x, y, 210, 34, alpha=0.45)
    cv2.circle(frame, (x + 16, y + 17), 5, color, -1, lineType=cv2.LINE_AA)
    cv2.putText(frame, text, (x + 30, y + 22), FONT_SMALL, 0.48, config.HUD_TEXT_COLOR, 1, cv2.LINE_AA)


# ---------------------------------------------------------------------- #
# Toast notifications (floating messages, e.g. "Canvas cleared")
# ---------------------------------------------------------------------- #
def draw_toasts(frame, messages):
    if not messages:
        return
    w = frame.shape[1]
    y = 120
    for msg in messages[-3:]:
        text_size = cv2.getTextSize(msg, FONT_SMALL, 0.6, 1)[0]
        panel_w = text_size[0] + 32
        x = (w - panel_w) // 2
        glass_panel(frame, x, y, panel_w, 36, alpha=0.6, border_color=(90, 230, 170))
        cv2.putText(frame, msg, (x + 16, y + 24), FONT_SMALL, 0.6, (230, 255, 240), 1, cv2.LINE_AA)
        y += 44


# ---------------------------------------------------------------------- #
# Keyboard shortcut help overlay (toggle with 'h')
# ---------------------------------------------------------------------- #
SHORTCUTS = [
    ("1-8", "Select color"),
    ("+ / -", "Increase / decrease brush size"),
    ("[ / ]", "Decrease / increase glow intensity"),
    ("U", "Undo last stroke"),
    ("C", "Clear canvas"),
    ("S", "Save drawing"),
    ("Space", "Extract text from drawing (OCR)"),
    ("V", "Toggle voice commands"),
    ("H", "Toggle this help overlay"),
    ("Q / Esc", "Quit application"),
]


def draw_help_overlay(frame):
    h, w = frame.shape[:2]
    panel_w, panel_h = 420, 40 + 28 * len(SHORTCUTS)
    x, y = (w - panel_w) // 2, (h - panel_h) // 2
    glass_panel(frame, x, y, panel_w, panel_h, alpha=0.78)
    cv2.putText(frame, "Keyboard Shortcuts", (x + 20, y + 34), FONT, 0.75, config.HUD_ACCENT, 1, cv2.LINE_AA)
    for i, (key, desc) in enumerate(SHORTCUTS):
        row_y = y + 66 + i * 28
        cv2.putText(frame, key, (x + 24, row_y), FONT_SMALL, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, desc, (x + 130, row_y), FONT_SMALL, 0.55, config.HUD_TEXT_COLOR, 1, cv2.LINE_AA)


# ---------------------------------------------------------------------- #
# Cursor indicator
# ---------------------------------------------------------------------- #
def draw_cursor(frame, point, gesture: str, thickness: int):
    if point is None:
        return
    color = (90, 230, 110) if gesture == "DRAW" else (150, 150, 165)
    cv2.circle(frame, point, max(6, thickness), color, 2, lineType=cv2.LINE_AA)
    cv2.circle(frame, point, 2, color, -1, lineType=cv2.LINE_AA)


# ---------------------------------------------------------------------- #
# Bottom-left title watermark
# ---------------------------------------------------------------------- #
def draw_watermark(frame):
    h = frame.shape[0]
    cv2.putText(frame, "GestureCanvas", (16, h - 16), FONT_SMALL, 0.5, config.HUD_MUTED_TEXT, 1, cv2.LINE_AA)
