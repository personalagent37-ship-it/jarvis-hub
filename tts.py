import asyncio
import tempfile
import os
import subprocess
import shutil
import threading
try:
    import edge_tts
except ImportError:
    edge_tts = None  # fallback to local TTS

try:
    import pyttsx3
except ImportError:
    # Minimal stub providing the same API used in the code.
    class _DummyPyttsx3:
        def init(self):
            # Returns self so that .say() and .runAndWait() can be called.
            return self
        def say(self, text):
            pass
        def runAndWait(self):
            pass
    pyttsx3 = _DummyPyttsx3()


from config import TTS_ENGINE, TTS_VOICE, TTS_VOICE_EN, TTS_VOICE_HI, TTS_RATE, TTS_VOLUME


class TextToSpeech:
    _lock = threading.Lock()
    def __init__(self):
        self.engine = TTS_ENGINE.lower()  # e.g., "edge" or "pyttsx3"
        self.voice = TTS_VOICE
        self.rate = TTS_RATE
        self.volume = TTS_VOLUME
        print(f"[TTS] Initialized: engine={self.engine}, voice={self.voice}, rate={self.rate}, volume={self.volume}")

    def speak(self, text: str):
        if not text or not text.strip():
            return
        # Ensure only one TTS playback at a time
        with self._lock:
            text = text.strip()
            if len(text) > 500:
                text = text[:500]
            # Choose voice based on language detection (Urdu vs English)
            if any('\u0600' <= ch <= '\u06FF' for ch in text):
                self.voice = TTS_VOICE_HI
            else:
                self.voice = TTS_VOICE_EN
            print(f"JARVIS: {text}")
            # Directly run async TTS (engine priority handled inside _speak_async)
            self._run_async(self._speak_async(text))

    def _run_async(self, coro):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)

        result = {}
        error = {}

        def target():
            try:
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                result["value"] = new_loop.run_until_complete(coro)
            except Exception as exc:
                error["exc"] = exc
            finally:
                try:
                    new_loop.close()
                except Exception:
                    pass

        thread = threading.Thread(target=target, daemon=True)
        thread.start()
        thread.join(timeout=60)
        if thread.is_alive():
            raise RuntimeError("TTS playback timed out")
        if error.get("exc"):
            raise error["exc"]
        return result.get("value")

    async def _speak_async(self, text: str):
        # Prefer Edge TTS (online) for high‑quality neural voice
        if edge_tts is not None and shutil.which("mpg123"):
            try:
                print("[TTS] Using edge_tts (online) as primary engine.")
                tts = edge_tts.Communicate(text, self.voice, rate=self.rate, volume=self.volume)
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                    tmpfile = f.name
                await asyncio.wait_for(tts.save(tmpfile), timeout=12)
                if os.path.getsize(tmpfile) > 0:
                    subprocess.run(["mpg123", "-q", tmpfile], timeout=15)
                    os.remove(tmpfile)
                    return
                os.remove(tmpfile)
            except Exception as e:
                print(f"[TTS] edge_tts failed: {e}")
        # Fallback to pyttsx3 (offline) if Edge is unavailable
        if pyttsx3 is not None:
            try:
                print("[TTS] Using pyttsx3 (offline) as fallback engine.")
                engine = pyttsx3.init()
                engine.say(text)
                engine.runAndWait()
                return
            except Exception as e:
                print(f"[TTS] pyttsx3 failed: {e}")
        # Try espeak / espeak-ng as last resort
        for cmd in (["espeak", "-s", "145", "-v", "en", text],
                    ["espeak-ng", "-s", "145", "-v", "en", text]):
            if shutil.which(cmd[0]):
                try:
                    print(f"[TTS] Using {cmd[0]} as fallback.")
                    subprocess.run(cmd, timeout=5, check=True)
                    return
                except Exception as e:
                    print(f"[TTS] {cmd[0]} failed: {e}")
        # Final fallback: console print
        print(f"[TTS] (fallback) {text}")
        return

    def _speak_local(self, text: str):
        """Legacy local fallback – kept for API compatibility.
        It now simply delegates to the async path for consistency.
        """
        # Directly call the async version in a blocking way
        try:
            self._run_async(self._speak_async(text))
            return True
        except Exception as e:
            print(f"[TTS] Local fallback failed: {e}")
            return False
