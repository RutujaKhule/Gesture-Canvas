"""
main.py
=======
GestureCanvas -- Desktop Edition
Entry point. Run with:

    python main.py

This owns the single OpenCV render loop: grab a webcam frame, track the
hand, update the drawing canvas and particle system, composite the neon
HUD, and handle keyboard shortcuts. See README.md for full usage details
and the in-app 'H' key for a live shortcut legend.
"""

import sys

import cv2

import config
import ui
from drawing import Canvas
from gesture import HandTracker, DRAW, STOP, NO_HAND
from particles import ParticleSystem
from ocr import extract_text
from voice import VoiceController, CLEAR, UNDO, SAVE, SET_COLOR, BRUSH_UP, BRUSH_DOWN, GLOW_UP, GLOW_DOWN, EXTRACT_TEXT, QUIT
from utils import FPSCounter, ToastQueue, ensure_dir


def open_camera():
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
    if not cap.isOpened():
        print(f"[GestureCanvas] ERROR: could not open camera index {config.CAMERA_INDEX}.")
        print("Check that a webcam is connected and not in use by another application,")
        print("or change CAMERA_INDEX in config.py.")
        sys.exit(1)
    return cap


def main():
    ensure_dir(config.SAVE_DIR)

    cap = open_camera()
    tracker = HandTracker()
    canvas = Canvas(config.FRAME_WIDTH, config.FRAME_HEIGHT)
    particles = ParticleSystem(config.FRAME_WIDTH, config.FRAME_HEIGHT)
    voice = VoiceController()
    fps_counter = FPSCounter()
    toasts = ToastQueue()

    ui.create_control_window()
    cv2.namedWindow(config.WINDOW_NAME, cv2.WINDOW_NORMAL)

    active_color_index = 0
    help_visible = False

    print("=" * 60)
    print(" GestureCanvas -- Desktop Edition")
    print(" Point your index finger up to draw. Make a fist to stop.")
    print(" Press 'H' inside the app window for the full shortcut list.")
    print("=" * 60)

    if not voice.available:
        print("[GestureCanvas] Note: SpeechRecognition/PyAudio not available -- "
              "voice commands are disabled. See README.md to enable them.")

    try:
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                print("[GestureCanvas] Warning: failed to read a frame from the camera.")
                continue

            if config.FLIP_CAMERA:
                frame = cv2.flip(frame, 1)
            frame = cv2.resize(frame, (config.FRAME_WIDTH, config.FRAME_HEIGHT))

            gesture, index_tip, landmarks_px, results = tracker.process(frame)
            hand_detected = gesture != NO_HAND

            # Pull live slider values from the native trackbar window.
            thickness, glow = ui.read_trackbars()
            canvas.set_thickness(thickness)
            canvas.set_glow_intensity(glow)

            # --- Drawing state machine -------------------------------------------------
            cursor_point = None
            if gesture == DRAW and index_tip is not None:
                if not canvas.is_drawing:
                    canvas.begin_stroke(index_tip)
                    cursor_point = index_tip
                else:
                    cursor_point = canvas.extend_stroke(index_tip)
                particles.emit_at(cursor_point, canvas.color)
            else:
                if canvas.is_drawing:
                    canvas.end_stroke()
                cursor_point = index_tip  # still show the cursor while stopped/hovering

            particles.spawn_ambient()
            particles.update()

            # --- Compositing -------------------------------------------------------
            composite = canvas.composite(frame)
            composite = cv2.add(composite, particles.render())
            tracker.draw_landmarks(composite, results)
            ui.draw_cursor(composite, cursor_point, gesture, canvas.thickness)

            # --- HUD -----------------------------------------------------------------
            fps = fps_counter.tick()
            ui.draw_status_hud(composite, fps, gesture, hand_detected)
            ui.draw_tool_hud(composite, canvas.color_name, canvas.color, canvas.thickness, canvas.glow_intensity)
            ui.draw_palette(composite, active_color_index)
            ui.draw_voice_indicator(composite, voice.is_listening, voice.available)
            ui.draw_toasts(composite, toasts.active())
            ui.draw_watermark(composite)
            if help_visible:
                ui.draw_help_overlay(composite)

            cv2.imshow(config.WINDOW_NAME, composite)

            # --- Voice commands (drained once per frame) ------------------------------
            quit_requested = False
            for command, params, transcript in voice.poll_commands():
                if command == CLEAR:
                    canvas.clear()
                    toasts.push("Voice: canvas cleared")
                elif command == UNDO:
                    canvas.undo()
                    toasts.push("Voice: undo")
                elif command == SAVE:
                    path = canvas.save(composite)
                    toasts.push(f"Voice: saved {path.split('/')[-1]}")
                elif command == SET_COLOR:
                    active_color_index = params["index"]
                    canvas.set_color_index(active_color_index)
                    toasts.push(f"Voice: color set to {params['name']}")
                elif command == BRUSH_UP:
                    canvas.change_thickness(2)
                    ui.sync_trackbars(canvas.thickness, canvas.glow_intensity)
                    toasts.push("Voice: brush increased")
                elif command == BRUSH_DOWN:
                    canvas.change_thickness(-2)
                    ui.sync_trackbars(canvas.thickness, canvas.glow_intensity)
                    toasts.push("Voice: brush decreased")
                elif command == GLOW_UP:
                    canvas.change_glow_intensity(1)
                    ui.sync_trackbars(canvas.thickness, canvas.glow_intensity)
                    toasts.push("Voice: glow increased")
                elif command == GLOW_DOWN:
                    canvas.change_glow_intensity(-1)
                    ui.sync_trackbars(canvas.thickness, canvas.glow_intensity)
                    toasts.push("Voice: glow decreased")
                elif command == EXTRACT_TEXT:
                    success, message = extract_text(canvas)
                    print(f"[OCR] {message}")
                    toasts.push("Voice: text extracted (see console)" if success else message[:60])
                elif command == QUIT:
                    quit_requested = True
                else:
                    toasts.push(f"Voice: didn't understand '{transcript}'")

            if quit_requested:
                break

            # --- Keyboard shortcuts ---------------------------------------------------
            key = cv2.waitKey(1) & 0xFF

            if key in (ord("q"), 27):  # Q or ESC
                break
            elif key == ord("c"):
                canvas.clear()
                toasts.push("Canvas cleared")
            elif key == ord("u"):
                applied = canvas.undo()
                toasts.push("Undo" if applied else "Nothing to undo")
            elif key == ord("s"):
                path = canvas.save(composite)
                toasts.push(f"Saved: {path.split('/')[-1]}")
                print(f"[GestureCanvas] Drawing saved to {path}")
            elif key == 32:  # Space
                success, message = extract_text(canvas)
                print(f"[OCR] {message}")
                toasts.push("Text extracted -- see console" if success else message[:70])
            elif key == ord("v"):
                listening = voice.toggle()
                toasts.push("Voice listening: ON" if listening else "Voice listening: OFF")
            elif key == ord("h"):
                help_visible = not help_visible
            elif key in (ord("+"), ord("=")):
                canvas.change_thickness(1)
                ui.sync_trackbars(canvas.thickness, canvas.glow_intensity)
            elif key in (ord("-"), ord("_")):
                canvas.change_thickness(-1)
                ui.sync_trackbars(canvas.thickness, canvas.glow_intensity)
            elif key == ord("["):
                canvas.change_glow_intensity(-1)
                ui.sync_trackbars(canvas.thickness, canvas.glow_intensity)
            elif key == ord("]"):
                canvas.change_glow_intensity(1)
                ui.sync_trackbars(canvas.thickness, canvas.glow_intensity)
            elif ord("1") <= key <= ord("8"):
                active_color_index = key - ord("1")
                canvas.set_color_index(active_color_index)

            # Allow closing via the window's native 'X' button too.
            if cv2.getWindowProperty(config.WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                break

    finally:
        voice.stop()
        tracker.close()
        cap.release()
        cv2.destroyAllWindows()
        print("[GestureCanvas] Session ended. Thanks for drawing!")


if __name__ == "__main__":
    main()
