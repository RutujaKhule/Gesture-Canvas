# GestureCanvas

**Draw in thin air.** GestureCanvas is a Python desktop application that turns your webcam into a virtual canvas: point your index finger to paint glowing neon strokes, make a fist to stop, and control everything else with keyboard shortcuts and your voice.

Built with OpenCV + MediaPipe Hands for real-time, GPU-free hand tracking — no external servers, no browser, no internet dependency beyond optional voice recognition.

---
#DEMO
## 🎥 Demo

![GestureCanvas Demo](demo.gif.mp4)
## ✨ Features

- **Live webcam tracking** via `cv2.VideoCapture()` with a real-time FPS counter
- **Index finger = Draw**, **Fist = Stop drawing** — a small, dependable gesture vocabulary
- **Persistent drawing canvas** that survives across frames, resizes, and sessions until cleared
- **Neon glowing strokes** with a real bloom/glow effect (Gaussian blur + additive blending)
- **Anti-gravity particles** that drift upward and fade from your brush tip while you draw
- **Floating ambient particles** for a living, futuristic background effect
- **8-color neon palette**, switchable with number keys `1`–`8`
- **Brush thickness slider** and **glow intensity slider** (native OpenCV trackbars)
- **Undo** (steps back through stroke history)
- **Clear canvas**
- **Save drawing** to `screenshots/` as a timestamped PNG
- **OCR text extraction** from your drawing/handwriting, triggered with `Space`
- **Voice commands** ("clear", "undo", "save", "red color", "bigger brush", …) via microphone
- **Smooth drawing interpolation** — exponential cursor smoothing + gap-filling interpolation so fast strokes never look broken
- **Beautiful futuristic glass-style HUD** — status badges, gesture indicator, color/brush panel, toast notifications, keyboard shortcut overlay
- **Keyboard shortcuts** for every non-gesture action

No Flask, no web server, no browser — just `python main.py`.

---


## 📦 Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/GestureCanvas.git
cd GestureCanvas
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

> **PyAudio note:** PyAudio needs PortAudio's development headers to build from source.
> - **Windows:** `pip install PyAudio` usually works directly with the prebuilt wheel above. If it fails, use `pip install pipwin && pipwin install pyaudio`.
> - **macOS:** `brew install portaudio` then `pip install PyAudio`.
> - **Linux (Debian/Ubuntu):** `sudo apt install portaudio19-dev python3-pyaudio` then `pip install PyAudio`.
>
> Voice commands are optional — if PyAudio/SpeechRecognition aren't installed, GestureCanvas detects this automatically and simply disables voice features with a console notice. Everything else still works.

### 4. Install Tesseract OCR (optional, for text extraction)

- **Windows:** download and run the installer from the [UB-Mannheim Tesseract build](https://github.com/UB-Mannheim/tesseract/wiki), then set `TESSERACT_CMD` in `config.py` to the install path if it isn't on your `PATH`.
- **macOS:** `brew install tesseract`
- **Linux (Debian/Ubuntu):** `sudo apt install tesseract-ocr`

If Tesseract isn't installed, pressing `Space` will show a clear message telling you what's missing instead of crashing.

### 5. Run it

```bash
python main.py
```

Two windows will open:
- **GestureCanvas** — the main camera + canvas view
- **GestureCanvas Controls** — brush thickness and glow intensity sliders

---

## 🎮 Usage

1. Sit in front of your webcam with your hand clearly visible.
2. **Point your index finger up** (all other fingers curled) to draw.
3. **Make a fist** to stop drawing and move your hand freely without leaving a trail.
4. Use the sliders in the **Controls** window to adjust brush thickness and glow intensity live.
5. Use number keys `1`–`8` to switch colors from the neon palette shown at the bottom of the window.
6. Press `H` any time for the full in-app shortcut legend.

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|---|---|
| `1`–`8` | Select a color from the palette |
| `+` / `-` | Increase / decrease brush thickness |
| `[` / `]` | Decrease / increase glow intensity |
| `U` | Undo last stroke |
| `C` | Clear the entire canvas |
| `S` | Save the current drawing to `screenshots/` |
| `Space` | Extract text from the drawing via OCR (printed to console + toast) |
| `V` | Toggle voice command listening on/off |
| `H` | Toggle the keyboard shortcut help overlay |
| `Q` / `Esc` | Quit the application |

## 🎙 Voice Commands

Press `V` to start listening, then say things like:

- "clear" / "new canvas"
- "undo"
- "save"
- "red color" / "blue color" / "green color" / "yellow color" / "orange color" / "cyan color" / "pink color" / "white color"
- "bigger brush" / "smaller brush"
- "more glow" / "less glow"
- "read text" / "extract text"
- "quit" / "exit"

Recognized commands appear as on-screen toasts; anything unrecognized is reported so you can rephrase.

---

## 📁 Project Structure

```
GestureCanvas/
│
├── main.py             # Entry point: the OpenCV render loop & keyboard handling
├── drawing.py           # Persistent canvas: strokes, glow/bloom, undo, save, OCR export
├── gesture.py            # MediaPipe hand tracking + DRAW/STOP gesture classification
├── particles.py           # Anti-gravity spark + ambient floating particle system
├── ui.py                   # Glass-style HUD: panels, badges, palette, sliders, toasts, help
├── ocr.py                   # Tesseract-based text extraction from the canvas
├── voice.py                  # Background microphone listener + voice command parsing
├── utils.py                   # FPS counter, interpolation, smoothing, toast queue
├── config.py                   # All tunable constants in one place
│
├── assets/                      # Static assets (icons, fonts, etc. if you add any)
├── screenshots/                  # Saved drawings land here (S key)
│
├── requirements.txt
├── README.md
├── LICENSE
└── .gitignore
```

---

## 🚀 Future Improvements

- Multi-hand support (two-handed drawing / gestures)
- Shape tools (rectangle, circle, line) via a secondary gesture
- AI-based shape auto-correction and drawing classification
- Layer system with per-layer opacity
- Export to SVG/PDF in addition to PNG
- Offline speech recognition (Vosk) as a fallback to the Google Web Speech API
- Custom on-screen gesture calibration wizard for different hand sizes/lighting

---

## License

Released under the [MIT License](LICENSE).
