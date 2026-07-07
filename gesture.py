"""
gesture.py
==========
Hand tracking and gesture classification, built on MediaPipe Hands.

GestureCanvas recognizes exactly two drawing gestures, kept deliberately
simple and reliable:

    Index finger only extended  -> DRAW
    Fist (no fingers extended)  -> STOP drawing

Every other action (undo, clear, save, color, brush size, glow, OCR,
voice) is driven by keyboard shortcuts (see ui.py / main.py), which keeps
the gesture vocabulary small and dependable even in modest lighting.
"""

import cv2
import mediapipe as mp

import config

# MediaPipe landmark indices used for finger-state detection.
WRIST = 0
THUMB_TIP, THUMB_IP = 4, 3
INDEX_TIP, INDEX_PIP = 8, 6
MIDDLE_TIP, MIDDLE_PIP = 12, 10
RING_TIP, RING_PIP = 16, 14
PINKY_TIP, PINKY_PIP = 20, 18
MIDDLE_MCP = 9

DRAW = "DRAW"
STOP = "STOP"
NO_HAND = "NO_HAND"


class HandTracker:
    """Wraps a MediaPipe Hands model and exposes a simple per-frame API."""

    def __init__(
        self,
        max_num_hands: int = config.MAX_NUM_HANDS,
        detection_confidence: float = config.DETECTION_CONFIDENCE,
        tracking_confidence: float = config.TRACKING_CONFIDENCE,
    ):
        self._mp_hands = mp.solutions.hands
        self._mp_drawing = mp.solutions.drawing_utils
        self._mp_styles = mp.solutions.drawing_styles
        self.hands = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )

    def rebuild(self, max_num_hands=None, detection_confidence=None, tracking_confidence=None):
        """Recreate the underlying model, e.g. after a confidence setting changes."""
        self.hands.close()
        self.hands = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands or config.MAX_NUM_HANDS,
            min_detection_confidence=detection_confidence or config.DETECTION_CONFIDENCE,
            min_tracking_confidence=tracking_confidence or config.TRACKING_CONFIDENCE,
        )

    def process(self, frame_bgr):
        """
        Run hand detection on a BGR frame.
        Returns (gesture, index_fingertip_px, landmarks_px, raw_results)
            gesture             : DRAW | STOP | NO_HAND
            index_fingertip_px  : (x, y) pixel coords, or None
            landmarks_px        : list of 21 (x, y) pixel tuples, or None
            raw_results         : the raw MediaPipe result (for drawing the skeleton)
        """
        h, w = frame_bgr.shape[:2]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = self.hands.process(rgb)
        rgb.flags.writeable = True

        if not results.multi_hand_landmarks:
            return NO_HAND, None, None, results

        hand_landmarks = results.multi_hand_landmarks[0]
        landmarks_px = [(int(lm.x * w), int(lm.y * h)) for lm in hand_landmarks.landmark]

        gesture = self._classify(landmarks_px)
        index_tip = landmarks_px[INDEX_TIP]
        return gesture, index_tip, landmarks_px, results

    @staticmethod
    def _finger_up(landmarks_px, tip_idx, pip_idx):
        return landmarks_px[tip_idx][1] < landmarks_px[pip_idx][1]

    def _classify(self, landmarks_px):
        index_up = self._finger_up(landmarks_px, INDEX_TIP, INDEX_PIP)
        middle_up = self._finger_up(landmarks_px, MIDDLE_TIP, MIDDLE_PIP)
        ring_up = self._finger_up(landmarks_px, RING_TIP, RING_PIP)
        pinky_up = self._finger_up(landmarks_px, PINKY_TIP, PINKY_PIP)

        if index_up and not middle_up and not ring_up and not pinky_up:
            return DRAW
        if not index_up and not middle_up and not ring_up and not pinky_up:
            return STOP
        # Any other hand pose (open palm, peace sign, etc.) simply pauses
        # drawing without being treated as an explicit "fist" -- this keeps
        # transitions between poses from ever drawing stray strokes.
        return STOP

    def draw_landmarks(self, frame_bgr, results):
        """Overlay the MediaPipe hand skeleton on the given frame (in place)."""
        if not results.multi_hand_landmarks:
            return
        for hand_landmarks in results.multi_hand_landmarks:
            self._mp_drawing.draw_landmarks(
                frame_bgr,
                hand_landmarks,
                self._mp_hands.HAND_CONNECTIONS,
                self._mp_drawing.DrawingSpec(color=config.HUD_ACCENT, thickness=2, circle_radius=3),
                self._mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=1),
            )

    def close(self):
        self.hands.close()
