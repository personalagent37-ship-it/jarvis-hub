import time
import os
import io
import base64
from vision import Vision
from config import DATA_DIR

vision = Vision()
SCREEN_PATH = os.path.join(DATA_DIR, "latest_screen.jpg")

print("==================================================")
print("[CONTEXT DAEMON] Starting Continuous Context Loop")
print("==================================================")

while True:
    try:
        # Take silent lightweight screenshot
        img = vision.get_screenshot()
        if img.mode != 'RGB':
            img = img.convert('RGB')
        # Compress it highly to save SSD space and i3 processor cycles
        img.save(SCREEN_PATH, format="JPEG", quality=40)
        
        # Audio Context Placeholder (Step 3 part 2)
        # We will integrate pyaudio stream here later to continuously buffer the last 30 seconds of audio.
        
    except Exception as e:
        print(f"[CONTEXT DAEMON ERROR] {e}")
    
    # Sleep for 10 seconds to keep CPU usage extremely low
    time.sleep(10)
