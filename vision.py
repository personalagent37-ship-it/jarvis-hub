import cv2
import mss

import base64
import io
from PIL import Image

class Vision:
    def __init__(self):
        try:
            self.sct = mss.mss()
        except Exception as e:
            self.sct = None
            print(f"[VISION] Screen capture unavailable: {e}")

    def _configure_camera(self, cap: cv2.VideoCapture) -> None:
        """Configure camera for low‑light conditions (flash, indoor)."""
        try:
            cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
            cap.set(cv2.CAP_PROP_EXPOSURE, -4)
        except Exception:
            pass
        try:
            cap.set(cv2.CAP_PROP_BRIGHTNESS, 0.6)
            cap.set(cv2.CAP_PROP_CONTRAST, 0.5)
        except Exception:
            pass

    def get_screenshot(self) -> Image.Image:
        try:
            if self.sct is None:
                raise RuntimeError("Screen capture via mss is unavailable")
            monitor = self.sct.monitors[1]
            screenshot = self.sct.grab(monitor)
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            img = img.resize((1280, 720), Image.LANCZOS)
            return img
        except Exception as e:
            print(f"[VISION] mss failed ({e}), falling back to subprocess screenshot tools...")
            import subprocess
            import tempfile
            import os
            
            env = os.environ.copy()
            if 'DISPLAY' not in env:
                env['DISPLAY'] = ':0'
                
            tmp_file = tempfile.mktemp(suffix=".png")
            
            # Try gnome-screenshot (Ubuntu default) then scrot
            try:
                subprocess.run(['gnome-screenshot', '-f', tmp_file], env=env, check=True, timeout=5)
            except Exception:
                try:
                    subprocess.run(['scrot', tmp_file], env=env, check=True, timeout=5)
                except Exception as e2:
                    raise RuntimeError(f"All screenshot methods failed: {e2}")
            
            img = Image.open(tmp_file)
            img = img.resize((1280, 720), Image.LANCZOS)
            return img

    def get_screen_b64(self) -> str:
        img = self.get_screenshot()
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=60)
        return base64.b64encode(buffer.getvalue()).decode()

    def save_screenshot(self, path: str = "/tmp/jarvis_screen.png"):
        img = self.get_screenshot()
        img.save(path)
        return path

    def get_screen_text(self) -> str:
        try:
            import pytesseract
            img = self.get_screenshot()
            return pytesseract.image_to_string(img)[:2000]
        except Exception:
            return "Could not read screen text"

    def get_camera_snapshot(self) -> str:
        """Capture a single frame from the default webcam and return a base64 JPEG.
        Applies low‑light configuration via _configure_camera to work with flash.
        """
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                print("[VISION] Webcam not found or unavailable")
                return ""
            # Apply low‑light settings
            self._configure_camera(cap)
            # Warm‑up sensor
            for _ in range(5):
                cap.read()
            ret, frame = cap.read()
            cap.release()
            if not ret:
                print("[VISION] Failed to capture camera frame")
                return ""
            # Resize for bandwidth
            frame = cv2.resize(frame, (800, 600))
            success, encoded_image = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not success:
                print("[VISION] JPEG encoding failed")
                return ""
            return base64.b64encode(encoded_image.tobytes()).decode('utf-8')
        except Exception as e:
            print(f"[VISION] Camera capture error: {e}")
            return ""

    def save_camera_snapshot(self, path: str = "/tmp/jarvis_camera.jpg") -> str:
        """Capture from webcam and save as image file."""
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return ""
            for _ in range(3):
                cap.read()
            ret, frame = cap.read()
            cap.release()
            if ret:
                cv2.imwrite(path, frame)
                return path
            return ""
        except Exception as e:
            print(f"[VISION] Save camera snapshot failed: {e}")
            return ""
