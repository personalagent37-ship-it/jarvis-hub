import time
import cv2
import subprocess
import os
import threading
try:
    import face_recognition
except ImportError:
    face_recognition = None

from tools.system_control import lock_screen, unlock_screen

# ==========================================
# ADVANCED SECURITY CONFIGURATION
# ==========================================
PASSWORD = "talha753159"
USER_FACE_IMAGE = "talha_face.jpg"  # Path to a picture of Talha
BLUETOOTH_MAC = ""  # Put your phone's Bluetooth MAC address here (e.g., "AA:BB:CC:DD:EE:FF")
# ==========================================

class IronManSecurity:
    def __init__(self):
        self.cap = None
        self.is_locked = False
        self.running = True
        self.talha_encoding = None
        self.ghost_proc = None
        
        # Try to load the user's face encoding
        self._load_user_face()
        
        # Start voice-activated lockdown thread
        # threading.Thread(target=self._camera_security_loop, daemon=True).start()
        # threading.Thread(target=self._voice_lockdown_listener, daemon=True).start() # Disabled for Zoom meetings

    def _load_user_face(self):
        if not face_recognition:
            print("[SECURITY] face_recognition library is still installing. Falling back to basic detection.")
            return

        if os.path.exists(USER_FACE_IMAGE):
            try:
                image = face_recognition.load_image_file(USER_FACE_IMAGE)
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    self.talha_encoding = encodings[0]
                    print("[SECURITY] Successfully loaded Talha's unique biometric signature!")
                else:
                    print("[SECURITY] Error: Could not find a face in the reference image.")
            except Exception as e:
                print(f"[SECURITY] Error loading face: {e}")
        else:
            print(f"[SECURITY] Warning: {USER_FACE_IMAGE} not found. Please put a picture of yourself in the jartvis folder named '{USER_FACE_IMAGE}'.")

    def enhance_night_vision(self, frame):
        """Enhance image brightness and contrast for dark environments."""
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl,a,b))
        enhanced = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        return enhanced

    def check_bluetooth_proximity(self):
        if not BLUETOOTH_MAC:
            return True # If no MAC provided, assume phone is always present
            
        try:
            # l2ping requires sudo usually, so we use hcitool name or bluetoothctl
            result = subprocess.run(["hcitool", "name", BLUETOOTH_MAC], capture_output=True, text=True, timeout=5)
            # If it returns a name, the device is in range
            if result.stdout.strip():
                return True
            return False
        except:
            return True

    def is_os_locked(self):
        try:
            result = subprocess.run(
                ["dbus-send", "--session", "--dest=org.gnome.ScreenSaver", 
                 "--type=method_call", "--print-reply", 
                 "/org/gnome/ScreenSaver", "org.gnome.ScreenSaver.GetActive"],
                capture_output=True, text=True, timeout=2
            )
            return "boolean true" in result.stdout
        except:
            return False

    def verify_talha_face(self):
        try:
            if not self.cap or not self.cap.isOpened():
                self.cap = cv2.VideoCapture(0)
            
            # Flush buffer to get newest frame
            for _ in range(5):
                self.cap.read()
                
            ret, frame = self.cap.read()
            if not ret:
                return False
                
            # Apply Night Vision Enhancement
            frame = self.enhance_night_vision(frame)
            
            # If face_recognition is installed and we have the signature, use strict matching
            if face_recognition and self.talha_encoding is not None:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb_frame)
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                
                for encoding in face_encodings:
                    # Strict tolerance for security (lower is stricter, 0.6 is default)
                    matches = face_recognition.compare_faces([self.talha_encoding], encoding, tolerance=0.55)
                    if True in matches:
                        return True
                return False
            else:
                # Fallback to basic Haar Cascade if no picture provided yet
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                faces = cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
                return len(faces) > 0
                
        except Exception as e:
            print(f"[SECURITY] Verification error: {e}")
            return False
        finally:
            # Turn off camera immediately to save battery and stop green light
            if self.cap:
                self.cap.release()
                self.cap = None

    def enable_ghost_mode(self):
        if not self.ghost_proc:
            env = os.environ.copy()
            if "DISPLAY" not in env:
                env["DISPLAY"] = ":0"
            if "XAUTHORITY" not in env:
                env["XAUTHORITY"] = "/home/talha/.Xauthority"
            self.ghost_proc = subprocess.Popen(["python3", "/home/talha/Desktop/jartvis/ghost_screen.py"], env=env)
            print("[SECURITY] Ghost Mode Activated! Screen blacked out.")

    def disable_ghost_mode(self):
        if self.ghost_proc:
            self.ghost_proc.kill()
            self.ghost_proc = None
            print("[SECURITY] Ghost Mode Deactivated!")

    def _voice_lockdown_listener(self):
        try:
            from wake_word import WakeWordDetector
            detector = WakeWordDetector(keyword="jarvis")
            print("[SECURITY] Voice-Activated Lockdown is listening...")
            while self.running:
                cmd = detector.listen_for_wake_word(chunk_duration=3.0)
                if isinstance(cmd, str) and "lockdown" in cmd.lower():
                    print("[SECURITY] VOICE LOCKDOWN TRIGGERED!")
                    lock_screen()
                    self.is_locked = True
                elif cmd is True:
                    # Heard Jarvis, but no command.
                    pass
        except Exception as e:
            print(f"[SECURITY] Voice listener error: {e}")

    def run(self):
        print("==================================================")
        print(" IRON MAN SECURITY PROTOCOL ONLINE")
        while self.running:
            phone_present = self.check_bluetooth_proximity()
            os_locked = self.is_os_locked()
            
            # Sync our internal lock state with the actual Ubuntu OS state
            if os_locked and not self.is_locked:
                print("[SECURITY] Detected manual OS lock.")
                self.is_locked = True
                
            if not phone_present and not self.is_locked:
                print("[SECURITY] Phone out of range! Initiating Ghost Mode...")
                self.enable_ghost_mode()
                self.is_locked = True
                
            elif self.is_locked:
                # If locked, check if phone came back in range OR just check camera every 3 seconds briefly
                if phone_present or not BLUETOOTH_MAC:
                    # Don't print "Checking for Talha's face..." constantly if it's not actually locked by OS.
                    # Actually, we want to unlock ghost mode AND OS lock!
                    is_talha = self.verify_talha_face()
                    if is_talha:
                        print("[SECURITY] Talha Verified! Unlocking system...")
                        self.disable_ghost_mode()
                        from tools.system_control import unlock_screen
                        unlock_screen("talha753159")
                        self.is_locked = False
                        
            time.sleep(3)
            
            # If no Bluetooth MAC is provided, we rely on the camera, but we wait MUCH longer
            # so it doesn't lock just because you looked away for a second!
            # if not self.is_locked and not BLUETOOTH_MAC:
            #     is_talha = self.verify_talha_face()
            #     if not is_talha:
            #         print("[SECURITY] User face lost. Waiting 15s grace period...")
            #         time.sleep(15)
            #         if not self.verify_talha_face():
            #             print("[SECURITY] User missing for 15+ seconds. Initiating Ghost Mode...")
            #             self.enable_ghost_mode()
            #             self.is_locked = True
            
            time.sleep(10)

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()

if __name__ == "__main__":
    security = IronManSecurity()
    try:
        security.run()
    except KeyboardInterrupt:
        security.stop()
