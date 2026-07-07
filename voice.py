"""
voice.py
========
Voice command support using SpeechRecognition (Google Web Speech API) with
PyAudio as the microphone backend. Listening runs on a background daemon
thread so it never blocks the main OpenCV render loop -- toggle it on/off
with the 'v' key.

Recognized phrases are parsed into a small, explicit command vocabulary
and pushed onto a thread-safe queue that main.py drains once per frame.
"""

import queue
import re
import threading

import config

try:
    import speech_recognition as sr
    VOICE_AVAILABLE = True
except ImportError:
    sr = None
    VOICE_AVAILABLE = False

# Command name constants
CLEAR = "CLEAR"
UNDO = "UNDO"
SAVE = "SAVE"
SET_COLOR = "SET_COLOR"
BRUSH_UP = "BRUSH_UP"
BRUSH_DOWN = "BRUSH_DOWN"
GLOW_UP = "GLOW_UP"
GLOW_DOWN = "GLOW_DOWN"
EXTRACT_TEXT = "EXTRACT_TEXT"
QUIT = "QUIT"
UNKNOWN = "UNKNOWN"

_COLOR_NAME_TO_INDEX = {name.split()[-1].lower(): i for i, (name, _) in enumerate(config.COLOR_PALETTE)}
_COLOR_NAME_TO_INDEX.update({
    "cyan": 0, "magenta": 1, "green": 2, "yellow": 3,
    "orange": 4, "blue": 5, "pink": 6, "white": 7,
})

_PATTERNS = [
    (CLEAR, [r"\bclear\b", r"\bnew canvas\b", r"\berase everything\b"]),
    (UNDO, [r"\bundo\b"]),
    (SAVE, [r"\bsave\b"]),
    (BRUSH_UP, [r"\bbigger brush\b", r"\bincrease brush\b", r"\bthicker\b"]),
    (BRUSH_DOWN, [r"\bsmaller brush\b", r"\bdecrease brush\b", r"\bthinner\b"]),
    (GLOW_UP, [r"\bmore glow\b", r"\bincrease glow\b", r"\bbrighter\b"]),
    (GLOW_DOWN, [r"\bless glow\b", r"\bdecrease glow\b", r"\bdimmer\b"]),
    (EXTRACT_TEXT, [r"\bread text\b", r"\bextract text\b", r"\bocr\b"]),
    (QUIT, [r"\bquit\b", r"\bexit\b", r"\bclose app\b"]),
]


def parse_command(transcript: str):
    """Parse a recognized transcript into (command_name, params_dict)."""
    text = transcript.lower().strip()

    color_match = re.search(r"\b(cyan|magenta|green|yellow|orange|blue|pink|white)\b", text)
    if "color" in text and color_match:
        name = color_match.group(1)
        return SET_COLOR, {"index": _COLOR_NAME_TO_INDEX.get(name, 0), "name": name}

    for command, patterns in _PATTERNS:
        for pattern in patterns:
            if re.search(pattern, text):
                return command, {}

    return UNKNOWN, {"raw": text}


class VoiceController:
    """Background microphone listener producing parsed commands on a queue."""

    def __init__(self):
        self._thread = None
        self._listening = threading.Event()
        self._command_queue = queue.Queue()
        self._recognizer = None
        self._last_error = None

        if VOICE_AVAILABLE:
            self._recognizer = sr.Recognizer()
            self._recognizer.energy_threshold = config.VOICE_ENERGY_THRESHOLD
            self._recognizer.dynamic_energy_threshold = True

    @property
    def available(self):
        return VOICE_AVAILABLE

    @property
    def is_listening(self):
        return self._listening.is_set()

    @property
    def last_error(self):
        return self._last_error

    def toggle(self):
        if self.is_listening:
            self.stop()
        else:
            self.start()
        return self.is_listening

    def start(self):
        if not VOICE_AVAILABLE or self.is_listening:
            return
        self._listening.set()
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._listening.clear()

    def _listen_loop(self):
        try:
            with sr.Microphone() as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.6)
                while self.is_listening:
                    try:
                        audio = self._recognizer.listen(
                            source,
                            timeout=config.VOICE_LISTEN_TIMEOUT,
                            phrase_time_limit=config.VOICE_PHRASE_TIME_LIMIT,
                        )
                    except sr.WaitTimeoutError:
                        continue
                    try:
                        transcript = self._recognizer.recognize_google(audio)
                    except sr.UnknownValueError:
                        continue
                    except sr.RequestError as exc:
                        self._last_error = f"Speech service error: {exc}"
                        continue
                    command, params = parse_command(transcript)
                    self._command_queue.put((command, params, transcript))
        except Exception as exc:  # pragma: no cover -- microphone/hardware dependent
            self._last_error = f"Microphone error: {exc}"
            self._listening.clear()

    def poll_commands(self):
        """Drain and return all commands recognized since the last poll."""
        commands = []
        while not self._command_queue.empty():
            commands.append(self._command_queue.get_nowait())
        return commands
